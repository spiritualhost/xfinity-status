#Get the status for xfinity service at your address without manual checks

#Import configparser for user-specified information
import configparser, usaddress, os, asyncio, sys, questionary, logging
from datetime import datetime
from playwright.async_api import async_playwright, Page

#Does the address appear to be legitimate (pre-check)
def validate_addr(address: str) -> tuple:
    try:
        tagged_addr = usaddress.tag(address)

        #Check that address number and street name are present at minimum
        return tagged_addr if (tagged_addr[0]["AddressNumber"] and tagged_addr[0]["StreetName"]) else 1

    #Most likely a RepeatedLabelError for ambiguous address structure
    except Exception as e:
        logging.info(f"Invalid address error: {e}")
        sys.exit(1)

#Write the address to the config file
async def addr_to_conf(address: str) -> str:
    if sys.stdout.isatty():
        if not await questionary.confirm(f"\nConfirm the address returned by the Xfinity portal is valid: {address} (y/n)").ask_async():
            logging.info("Error: please retry address entry.")
            sys.exit(1)
    else:
        logging.info(f"Non-interactive mode, auto accepting resolved address {address}")

    try:
        config = configparser.ConfigParser()
        config.read("config.ini")
        
        #Set up and write to config
        config["Settings"]["address"] = address

        with open("config.ini", "w") as configfile:
            config.write(configfile)
        
        logging.info(f"Address {address} written to config successfully.")

    except Exception as e:
        logging.info(f"Config error: {e}")
        sys.exit(1)

#Loading animation
async def loading(default_message="Loading, please wait"):
    #Skip animation if not in terminal
    if sys.stdout.isatty():
        chars = ['⣾', '⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽']
        while True:
            for i in chars:
                sys.stdout.write(f"\r{default_message} {i}")
                sys.stdout.flush()
                await asyncio.sleep(.1)

#Get current status from Xfinity
async def current_status(page: Page) -> str:
    try:
        #Strip page status
        return await page.locator("prism-text[display='heading3']").first.inner_text()

    except Exception as e:
        logging.info(f"Status error: {e}")
        sys.exit(1)

#Enter address
async def enter_addr(page: Page, address: str):
 
    try:      
        #Set up loading animation for confirmation of page reached
        load_ani = asyncio.create_task(loading("Page reached, attempting to enter provided address, please wait..."))

        #Wait for combobox to load fully, click into it, then enter input service address as a string
        await page.wait_for_selector('[role="combobox"]')
        await page.get_by_role('combobox', name="Enter service address").click()
        await page.keyboard.insert_text(address)

        #Simulate human typing so autocomplete dropdown appears
        await page.keyboard.press("Space")
        await page.keyboard.press("Backspace")

        #Wait for suggested addresses
        await page.wait_for_selector('#typeaheadResults')

        #Grab the canonical stored value that Xfinity returned for comparison to the originally user-entered address
        resolved = await page.get_by_test_id("serviceAddress0").inner_text()

        load_ani.cancel()
        #Clean up task
        try:
            await load_ani
        except asyncio.CancelledError:
            pass
        
        config = configparser.ConfigParser()
        config.read("config.ini")
        if not config["Settings"]["address"]:
            if not sys.stdin.isatty():
                logging.info("No address in config. Run interactively first or add address manually to config file.")
                sys.exit(1)
            #Confirm that address on page is correct, write to config
            await addr_to_conf(resolved)

        #Select first address on page
        await page.get_by_test_id("serviceAddress0").click()

    except Exception as e:
        logging.info(f"Error on address entry: {e}")
        sys.exit(1)

#Asynchronously open the web browser
async def open_browser(address: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        load_ani = asyncio.create_task(loading("Loading headless browser launch, please wait..."))
        await page.goto("https://www.xfinity.com/support/statusmap")
        load_ani.cancel()

        #Clean up task
        try:
            await load_ani
        except asyncio.CancelledError:
            pass
                
        #Control flow set up so keyboard interrupt happens cleanly
        try:
            while True:
                #Attempt to enter the address on the page after waiting for it to fully load
                await page.wait_for_load_state("load")
                await enter_addr(page, address)
                
                #Get current status from status page
                status = await current_status(page)
                if not sys.stdout.isatty(): #If non-interactive
                    logging.info(status)
                else:
                    print(f"\n{datetime.now()} {status}")            

                #Reload and try again after wait
                config = configparser.ConfigParser()
                config.read("config.ini")
                sleep_time = int(config["Settings"]["sleep"])
                load_ani = asyncio.create_task(loading(f"Waiting {sleep_time} seconds until the next check, please wait..."))
                await asyncio.sleep(sleep_time)
                load_ani.cancel()

                #Clean up task
                try:
                   await load_ani
                except asyncio.CancelledError:
                    pass

                await page.reload()
        
        except Exception as e:
            logging.info(f"Flow error: {e}")

        finally:
            try:
                logging.info("Program closing, please wait...") 
                await browser.close()
            except Exception:
                pass

if __name__ == "__main__":

    #Set up logging format
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )

    #Go through onboarding steps if they didn't happen already
    if not os.path.exists("config.ini"):

        #Initialize config file structure
        config = configparser.ConfigParser()
        config['Settings'] = {
            'address': '',
            'sleep': '1800' #Sleep for 30 minutes (1800) by default
        }
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        #Additional non-interactivity check
        if not sys.stdin.isatty():
            logging.info("No address configured. Please run interactively to set up, or add your address manually to config.ini.")
            sys.exit(1)

        #Get service address for business and perform initial validation
        serv_addr = input("What is the service address for the business, including the zip code: ").strip()
        if validate_addr(serv_addr) == 1:
            logging.info("Address validation failed. Please enter a valid address.")
            sys.exit(1)

    #Read already created config file
    else:
        config = configparser.ConfigParser()
        config.read("config.ini")
        serv_addr = config["Settings"]["address"]    
        if not serv_addr:
            logging.info("No address configured. Please run interactively to set up, or add your address manually to config.ini.")
            sys.exit(1)

    #Open a headless web browser
    try:
        asyncio.run(open_browser(serv_addr))
    except KeyboardInterrupt:
        pass
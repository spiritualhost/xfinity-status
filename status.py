#Get the status for xfinity service at your address without manual checks

#Import configparser for user-specified information
import configparser, usaddress, os, asyncio, sys
from playwright.async_api import async_playwright, Page

#Does the address appear to be legitimate (pre-check)
def validate_addr(address: str) -> tuple:
    try:
        tagged_addr = usaddress.tag(address)
        print(tagged_addr)
        print(tagged_addr[0]["AddressNumber"])

        #Check that address number and street name are present at minimum
        return tagged_addr if (tagged_addr[0]["AddressNumber"] and tagged_addr[0]["StreetName"]) else 1

    #Most likely a RepeatedLabelError for ambiguous address structure
    except Exception as e:
        print(f"Invalid address error: {e}")
        sys.exit(1)

#Write the address to the config file
def addr_to_conf(address: tuple):
    return 0

#Loading animation
async def loading(default_message="Loading, please wait"):
    chars = ['⣾', '⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽']
    while True:
        for i in chars:
            sys.stdout.write(f"\r{default_message} {i}")
            sys.stdout.flush()
            await asyncio.sleep(.1)

#Enter address
async def enter_addr(page: Page, address: str):
    #Set up loading animation for confirmation of page reached
    load_ani = asyncio.create_task(loading("Page reached, attempting to enter provided address, please wait..."))

    try:      
        #Wait for combobox to load fully, click into it, then enter input service address as a string
        await page.wait_for_selector('[role="combobox"]')
        await page.get_by_role('combobox', name="Enter service address").click()
        #await page.keyboard.type(address, delay=300)
        await page.keyboard.insert_text(address)

        #Simulate human typing so autocomplete dropdown appears
        await page.keyboard.press("Space")
        await page.keyboard.press("Backspace")



        #Wait for suggested addresses
        await page.wait_for_selector('#typeaheadResults')

        #Grab the canonical stored value that Xfinity returned for comparison to the originally user-entered address
        resolved = await page.get_by_test_id("serviceAddress0").inner_text()
        print(resolved)

        #Select first address on page
        await page.get_by_test_id("serviceAddress0").click()



    except Exception as e:
        print(f"Error on address entry: {e}")
        sys.exit(1)
    
    finally:
        #Cut off animation when address entered
        load_ani.cancel()
        
        #Clean up task
        try:
            await load_ani
        except asyncio.CancelledError:
            pass


#Asynchronously open the web browser
async def open_browser(address: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        load_ani = asyncio.create_task(loading("Loading headless browser launch, please wait..."))
        await page.goto("https://www.xfinity.com/support/statusmap")
        load_ani.cancel()

        #Clean up task
        try:
            await load_ani
        except asyncio.CancelledError:
            pass
        
        #Attempt to enter the address on the page after waiting for it to fully load
        await page.wait_for_load_state("load")
        await enter_addr(page, address)

        await browser.close()



if __name__ == "__main__":

    #Get service address for business and perform initial validation
    serv_addr = input("What is the service address for the business, including the zip code: ")
    returned_valid = validate_addr(serv_addr)
    
    #Update config file
    addr_to_conf(returned_valid)

    #Open a headless web browser
    asyncio.run(open_browser(serv_addr))

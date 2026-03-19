#Get the status for xfinity service at your address without manual checks

#Import configparser for user-specified information
import configparser, usaddress, os, asyncio, time, sys
from playwright.async_api import async_playwright

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
        os._exit(1)

#Loading animation
async def loading():
    chars = ['⣾', '⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽']
    while True:
        for i in chars:
            sys.stdout.write(f"\rLoading, please wait {i}")
            sys.stdout.flush()
            await asyncio.sleep(.1)

#Asynchronously open the web browser
async def open_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        load_ani = asyncio.create_task(loading())
        await page.goto("https://www.xfinity.com/support/statusmap")
        load_ani.cancel()

        #Clean up task
        try:
            await load_ani
        except asyncio.CancelledError:
            pass

        print(f"\nPage title: {await page.title()}")
        await browser.close()



if __name__ == "__main__":

    #Get service address for business and perform initial validation
    serv_addr = input("What is the service address for the business, including the zip code: ")
    returned_valid = validate_addr(serv_addr)

    #Open a headless web browser
    asyncio.run(open_browser())

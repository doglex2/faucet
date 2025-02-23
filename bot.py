import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2
from config import ANTI_CAPTCHA_KEY, FAUCET_URL

# Konfigurasi logging
logging.basicConfig(filename="faucet_bot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def get_wallet_address():
    with open("wallet.txt", "r") as file:
        return file.read().strip()

def solve_recaptcha(site_key, url):
    solver = recaptchaV2()
    solver.set_key(ANTI_CAPTCHA_KEY)
    solver.set_website_url(url)
    solver.set_website_key(site_key)
    
    logging.info("Mengirim reCAPTCHA ke Anti-Captcha...")
    token = solver.solve_and_return_solution()
    
    if token:
        logging.info("reCAPTCHA berhasil diselesaikan!")
        return token
    else:
        logging.error("Gagal menyelesaikan reCAPTCHA: %s", solver.error_code)
        return None

def claim_faucet():
    driver = setup_driver()
    driver.get(FAUCET_URL)
    time.sleep(3)
    
    # Ambil site-key reCAPTCHA dari halaman
    site_key_element = driver.find_element(By.XPATH, "//div[@class='g-recaptcha']")
    site_key = site_key_element.get_attribute("data-sitekey")
    
    if not site_key:
        logging.error("Site-key reCAPTCHA tidak ditemukan!")
        driver.quit()
        return
    
    # Ambil alamat dompet dari file wallet.txt
    wallet_address = get_wallet_address()
    input_box = driver.find_element(By.NAME, "address")
    input_box.send_keys(wallet_address)
    
    # Selesaikan reCAPTCHA
    recaptcha_token = solve_recaptcha(site_key, FAUCET_URL)
    if recaptcha_token:
        driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML = "{recaptcha_token}";')
        time.sleep(2)
    else:
        logging.error("Gagal mendapatkan token reCAPTCHA!")
        driver.quit()
        return
    
    # Klik tombol claim
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    submit_button.click()
    logging.info("Klaim faucet berhasil dikirim!")
    
    driver.quit()

def main():
    while True:
        logging.info("Menjalankan bot faucet...")
        claim_faucet()
        logging.info("Menunggu 24 jam sebelum klaim berikutnya...")
        time.sleep(86400)  # Tunggu 24 jam

if __name__ == "__main__":
    main()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import logging
import requests
import base64
import os

# Konfigurasi logging
logging.basicConfig(filename="faucet_bot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# API Key Gemini (Ganti dengan API Key Anda)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro-vision:generateContent?key=" + GEMINI_API_KEY

# Baca alamat wallet dari file
WALLET_FILE = "wallet.txt"
if not os.path.exists(WALLET_FILE):
    logging.error("File wallet.txt tidak ditemukan!")
    exit("File wallet.txt tidak ditemukan! Buat file tersebut dan masukkan alamat wallet Anda.")

with open(WALLET_FILE, "r") as f:
    WALLET_ADDRESS = f.read().strip()

def solve_captcha(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    payload = {
        "contents": [{
            "parts": [{"mimeType": "image/png", "data": encoded_image}]
        }]
    }
    
    response = requests.post(GEMINI_API_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        captcha_text = result.get("candidates", [{}])[0].get("content", "").strip()
        logging.info(f"CAPTCHA yang dikenali: {captcha_text}")
        return captcha_text
    else:
        logging.error("Gagal menyelesaikan CAPTCHA dengan Gemini: %s", response.text)
        return ""

def claim_faucet():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Mode tanpa GUI untuk VPS
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    driver.get("https://sepolia-faucet.pk910.de/")
    time.sleep(3)  # Tunggu halaman termuat

    try:
        # Screenshot CAPTCHA
        captcha_element = driver.find_element(By.XPATH, "//img[contains(@src, 'captcha')]")
        captcha_path = "captcha.png"
        captcha_element.screenshot(captcha_path)
        logging.info("Captcha tersimpan sebagai captcha.png")

        # Gunakan Gemini untuk membaca CAPTCHA
        captcha_code = solve_captcha(captcha_path)
        if not captcha_code:
            logging.error("CAPTCHA tidak bisa dikenali, hentikan proses.")
            driver.quit()
            return
    except Exception as e:
        logging.error("Gagal mengambil CAPTCHA: %s", e)
        driver.quit()
        return

    # Memasukkan alamat wallet
    wallet_input = driver.find_element(By.NAME, "address")  # Ganti dengan selector yang sesuai
    wallet_input.send_keys(WALLET_ADDRESS)

    # Memasukkan jumlah ETH (maks 2.5 ETH Sepolia)
    amount_input = driver.find_element(By.NAME, "amount")  # Ganti dengan selector yang sesuai
    amount_input.send_keys("2.5")

    # Memasukkan CAPTCHA
    captcha_input = driver.find_element(By.NAME, "captcha")  # Ganti dengan selector yang sesuai
    captcha_input.send_keys(captcha_code)

    # Klik tombol submit
    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")  # Ganti dengan selector yang sesuai
    submit_button.click()

    logging.info("Faucet diklaim sebesar 2.5 ETH Sepolia!")
    print("Faucet diklaim! Cek saldo wallet Anda.")

    time.sleep(5)  # Tunggu beberapa detik sebelum menutup
    driver.quit()
    
    # Hapus file CAPTCHA setelah digunakan
    if os.path.exists(captcha_path):
        os.remove(captcha_path)
        logging.info("Captcha.png dihapus setelah diproses.")

def main():
    while True:
        logging.info("Menjalankan bot faucet...")
        claim_faucet()
        logging.info("Menunggu 24 jam sebelum klaim berikutnya...")
        time.sleep(86400)  # Tunggu 24 jam

if __name__ == "__main__":
    main()

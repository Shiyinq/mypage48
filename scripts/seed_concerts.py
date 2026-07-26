import asyncio
import os
import sys

# Add the root directory to PYTHONPATH so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from src.config import config


CONCERTS_DATA = [
    {
        "title": "JKT48 1st Anniversary Event (2012)",
        "theme": "-",
        "type": "Anniversary",
        "date": "2012-12-23T19:00:00Z",
        "location": "Gedung Bulutangkis Senayan, Jakarta Pusat",
        "details": "Dirayakan secara relatif sederhana menandai setahun sejak debut JKT48 di televisi. Konser ini menampilkan Generasi 1 (yang kemudian menjadi Tim J) dan Generasi 2.",
        "benefits": [],
        "ticket_price": [
            "Umum/Reguler: Estimasi Rp 100.000 - Rp 250.000 (Data arsip resmi per kategori tidak tersedia secara publik)"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=1st+Anniversary"
    },
    {
        "title": "JKT48 2nd Anniversary Concert (2013)",
        "theme": "Performing All Out! Terima Kasih Telah Menjadi Temanku!!",
        "type": "Anniversary",
        "date": "2013-12-21T19:00:00Z",
        "location": "Plenary Hall, Jakarta Convention Center (JCC), Jakarta",
        "details": "Merupakan konser besar pertama ulang tahun JKT48. Digelar dalam 2 pertunjukan (Show 1 dan Show 2) dalam satu hari. Diwarnai dengan kelulusan anggota (Stella, Sonya, Diasta).",
        "benefits": [],
        "ticket_price": [
            "VIP: Rp 330.000",
            "Festival A: Rp 220.000",
            "Festival B: Rp 165.000",
            "Tribune A: Rp 165.000",
            "Tribune B: Rp 55.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=2nd+Anniversary"
    },
    {
        "title": "JKT48 3rd Anniversary Concert (2014)",
        "theme": "Saya Masih Anak Kecil",
        "type": "Anniversary",
        "date": "2014-12-27T19:00:00Z",
        "location": "Tennis Indoor Senayan, Jakarta",
        "details": "Konser digelar selama 2 hari berturut-turut. Di sini Generasi 3 yang masih berstatus siswi pelatihan ikut unjuk gigi bersanding dengan senior mereka.",
        "benefits": [
            "Pemegang tiket VIP mendapatkan gimmick/suvenir spesial."
        ],
        "ticket_price": [
            "VIP: Rp 880.000",
            "Tribun Tengah: Rp 275.000",
            "Festival: Rp 220.000",
            "Tribun Kiri-Kanan: Rp 198.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=3rd+Anniversary"
    },
    {
        "title": "JKT48 4th Anniversary Theater Event (2015)",
        "theme": "-",
        "type": "Anniversary",
        "date": "2015-12-17T19:00:00Z",
        "location": "Teater JKT48, fX Sudirman, Jakarta",
        "details": "Tahun ini perayaan difokuskan sebagai perayaan intim di Teater JKT48 bersama para fans setia. Pada tahun yang sama, JKT48 juga menggelar banyak tur dan acara tahun baru.",
        "benefits": [],
        "ticket_price": [
            "Tiket Teater Spesial: Kisarannya Rp 100.000 - Rp 150.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=4th+Anniversary"
    },
    {
        "title": "JKT48 5th Anniversary Concert (2016) and Haruka Nakagawa Graduation Ceremony",
        "theme": "B•E•L•I•E•V•E",
        "type": "Anniversary",
        "date": "2016-12-17T19:00:00Z",
        "location": "Trans Luxury Convention Center, Bandung, Jawa Barat",
        "details": "Konser ulang tahun pertama yang diadakan di luar Jakarta. Konser ini juga menjadi momen perpisahan emosional (Graduation Ceremony) untuk Haruka Nakagawa.",
        "benefits": [
            "Kategori DIAMOND mendapatkan T-shirt original, DVD konser, & sesi foto grup bersama member."
        ],
        "ticket_price": [
            "DIAMOND: Rp 800.000",
            "GOLD: Rp 280.000",
            "SILVER: Rp 180.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=5th+Anniversary"
    },
    {
        "title": "JKT48 6th Anniversary Birthday Party (2017)",
        "theme": "-",
        "type": "Anniversary",
        "date": "2017-12-23T19:00:00Z",
        "location": "JIExpo Kemayoran, Jakarta (Bagian dari Big Bang Jakarta 2017)",
        "details": "Alih-alih konser solo besar, ulang tahun ke-6 dirayakan secara meriah dalam panggung festival musik akhir tahun.",
        "benefits": [],
        "ticket_price": [
            "Tiket Masuk Pameran/Festival Big Bang: Rp 30.000 - Rp 50.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=6th+Anniversary"
    },
    {
        "title": "JKT48 7th Anniversary Concert (2018)",
        "theme": "7th Anniversary",
        "type": "Anniversary",
        "date": "2018-12-22T19:00:00Z",
        "location": "Balai Sarbini, Jakarta",
        "details": "Menggelar rangkaian roadshow di Surabaya sebelum acara perayaan puncaknya di Jakarta.",
        "benefits": [],
        "ticket_price": [
            "Reguler/Silver: Rp 250.000",
            "VIP/Platinum: Rp 750.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=7th+Anniversary"
    },
    {
        "title": "JKT48 8th Anniversary Concert (2019)",
        "theme": "-",
        "type": "Anniversary",
        "date": "2019-12-22T19:00:00Z",
        "location": "Tunjungan Plaza Convention Hall, Surabaya, Jawa Timur",
        "details": "JKT48 kembali ke luar kota untuk merayakan hari jadinya, kali ini di markas besar fanbase Jawa Timur, yaitu Surabaya.",
        "benefits": [],
        "ticket_price": [
            "Estimasi harga berkisar antara Rp 200.000 hingga Rp 600.000."
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=8th+Anniversary"
    },
    {
        "title": "JKT48 9th Anniversary Concert (2020)",
        "theme": "SOL/LUNA",
        "type": "Anniversary",
        "date": "2020-12-18T19:00:00Z",
        "location": "Studio 14 RCTI+ MNC Studios, Jakarta",
        "details": "Dirayakan di tengah pandemi COVID-19, konser ini disiarkan secara live streaming berbayar. Konser ini juga menandai kelulusan beberapa member senior legendaris seperti Beby, Frieska, Nadila, Rona, dan Desy.",
        "benefits": [],
        "ticket_price": [
            "Tiket Live Streaming (RCTI+ / Mister Aladin): Mulai dari Rp 55.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=9th+Anniversary"
    },
    {
        "title": "JKT48 10th Anniversary Kick-Off Conference & Concert (2021 - 2022)",
        "theme": "HEAVEN",
        "type": "Anniversary",
        "date": "2022-08-06T19:00:00Z",
        "location": "Istora Senayan, Jakarta",
        "details": "Untuk perayaan 1 dekade, JKT48 melakukan Kick-Off pengumuman di tahun 2021. Puncak konser 10 tahunnya sendiri digelar spektakuler di Istora Senayan pertengahan 2022, sekaligus menjadi perayaan kelulusan Gaby, anggota Generasi 1 terakhir.",
        "benefits": [],
        "ticket_price": [
            "Zeus (VIP): Rp 1.200.000",
            "Poseidon: Rp 500.000",
            "Apollo: Rp 300.000",
            "Artemis: Rp 250.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=10th+Anniversary"
    },
    {
        "title": "JKT48 11th Anniversary Concert (2022)",
        "theme": "Flying High",
        "type": "Anniversary",
        "date": "2022-12-17T19:00:00Z",
        "location": "Marina Convention Center, Semarang, Jawa Tengah",
        "details": "Konser meriah yang dibawa ke Semarang. Merayakan keberhasilan New Era JKT48 yang sedang memuncak popularitasnya lewat single Flying High.",
        "benefits": [],
        "ticket_price": [
            "Tercatat ke-13.000 tiket terjual habis (sold out) dengan estimasi harga dari Rp 250.000 hingga Rp 800.000."
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=11th+Anniversary"
    },
    {
        "title": "JKT48 12th Anniversary Concert (2023)",
        "theme": "FLOWERFUL",
        "type": "Anniversary",
        "date": "2023-12-17T19:00:00Z",
        "location": "Graha UNESA Surabaya, Jawa Timur",
        "details": "JKT48 menyapa kembali penggemarnya di Surabaya dengan panggung megah bertemakan bunga (Flowerful) yang melambangkan member JKT48 yang terus bermekaran.",
        "benefits": [],
        "ticket_price": [
            "Rose: Rp 1.100.000 (Presale) / Rp 1.300.000 (Normal)",
            "Orchid: Rp 650.000 (Presale) / Rp 750.000 (Normal)",
            "Tulip: Rp 500.000 (Presale) / Rp 600.000 (Normal)",
            "Jasmine Floor: Rp 280.000 (Presale) / Rp 350.000 (Normal)",
            "Jasmine Tribune: Rp 280.000 (Presale) / Rp 350.000 (Normal)"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=12th+Anniversary"
    },
    {
        "title": "JKT48 13th Anniversary Concert (2024) & Sousenkyo Announcement",
        "theme": "Wonderland",
        "type": "Anniversary",
        "date": "2024-12-15T19:00:00Z",
        "location": "Indonesia Arena, Gelora Bung Karno (GBK), Jakarta Pusat",
        "details": "Skala konser paling masif dalam sejarah JKT48, diadakan di Indonesia Arena yang mampu menampung belasan ribu penonton. Digabung dengan pengumuman hasil akhir pemilihan Senbatsu (Sousenkyo) ke-26.",
        "benefits": [
            "Kategori CAT 1 (Khusus OFC) mendapatkan akses soundcheck, signed polaroid, bonus serial code Sousenkyo, dan merchandise.",
            "Kategori CAT 2 mendapatkan bonus serial code Sousenkyo & merchandise."
        ],
        "ticket_price": [
            "CAT 1: Rp 4.800.000 (Khusus OFC)",
            "CAT 2: Rp 2.000.000",
            "CAT 3, CAT 4, dsb: Bervariasi di kisaran Rp 300.000 hingga Rp 850.000"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=13th+Anniversary"
    },
    {
        "title": "JKT48 14th Anniversary Concert (2025)",
        "theme": "THE FIRST SNOW",
        "type": "Anniversary",
        "date": "2025-12-20T19:00:00Z",
        "location": "Hall 1 & 2, ICE (Indonesia Convention Exhibition) BSD City, Tangerang",
        "details": "Perayaan 14 tahun JKT48 yang mengambil tema musim dingin (Snow). Diadakan di hall pameran terbesar di Indonesia (ICE BSD).",
        "benefits": [
            "Kategori CAT 1 (Khusus OFC) mendapatkan benefit eksklusif tiket teater pertunjukan terakhir Gracia JKT48."
        ],
        "ticket_price": [
            "CAT 1: Rp 3.000.000 (Hanya Presale OFC)",
            "CAT 2: Rp 1.900.000 (Presale OFC) / Rp 2.000.000 (Umum)",
            "CAT 3: Rp 1.400.000 (Presale OFC) / Rp 1.500.000 (Umum)",
            "CAT 4: Rp 900.000 (Presale OFC) / Rp 1.000.000 (Umum)",
            "CAT 5: Rp 700.000 (Presale OFC) / Rp 750.000 (Umum)",
            "CAT 6: Rp 550.000 (Presale OFC) / Rp 600.000 (Umum)",
            "CAT 7: Rp 500.000 (Khusus Umum)",
            "CAT 8: Rp 400.000 (Khusus Umum)"
        ],
        "image": "https://placehold.co/600x800/2a2a2a/ffffff?text=14th+Anniversary"
    }
]

async def seed_db():
    print(f"Connecting to MongoDB at {config.mongo_uri}...")
    client = AsyncIOMotorClient(config.mongo_uri)
    db = client[config.db_name]
    
    collection = db["concerts"]
    
    # Optional: Clear existing concerts if you want to rerun this script safely
    await collection.delete_many({})
    
    result = await collection.insert_many(CONCERTS_DATA)
    print(f"Successfully seeded {len(result.inserted_ids)} concerts into '{config.db_name}.concerts'")

if __name__ == "__main__":
    asyncio.run(seed_db())

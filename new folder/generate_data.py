"""
Thibitisha Synthetic Data Generator
Generates realistic Kenyan subscriber data for development and demo purposes.
NO REAL DATA. All MSISDNs, IDs, and names are fake.
"""
import json
import random
import hashlib
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_KE')

# Kenyan MNO prefixes
MNO_PREFIXES = {
    'safaricom': ['254701', '254702', '254703', '254704', '254705', '254706', '254707', '254708', '254709', '254710', '254711', '254712', '254713', '254714', '254715', '254716', '254717', '254718', '254719', '254720', '254721', '254722', '254723', '254724', '254725', '254726', '254727', '254728', '254729'],
    'airtel': ['254730', '254731', '254732', '254733', '254734', '254735', '254736', '254737', '254738', '254739', '254750', '254751', '254752', '254753', '254754', '254755', '254756', '254757', '254758', '254759'],
    'telkom': ['254770', '254771', '254772', '254773', '774', '775', '776'],
    'faiba': ['254747', '254743']
}

KENYAN_COUNTIES = [
    'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Kiambu', 'Machakos',
    'Kajiado', 'Nyeri', 'Meru', 'Kakamega', 'Kisii', 'Bungoma', 'Busia',
    'Kericho', 'Bomet', 'Narok', 'Kilifi', 'Kwale', 'Lamu', 'Taita Taveta',
    'Garissa', 'Wajir', 'Mandera', 'Marsabit', 'Isiolo', 'Meru', 'Tharaka Nithi',
    'Embu', 'Kitui', 'Makueni', 'Nyandarua', 'Nyeri', 'Kirinyaga', 'Murang'a'
]


def generate_msisdn(mno=None):
    """Generate a fake Kenyan MSISDN."""
    if mno is None:
        mno = random.choice(list(MNO_PREFIXES.keys()))
    prefix = random.choice(MNO_PREFIXES[mno])
    # Fill remaining digits to make 12 digits total (254 + 9 digits)
    remaining = 12 - len(prefix)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(remaining)])
    return prefix + suffix


def generate_id_number():
    """Generate a fake Kenyan ID number (8 digits)."""
    return str(random.randint(10000000, 39999999))


def hash_msisdn(msisdn, salt="thibitisha_dev_salt_2026"):
    """Hash an MSISDN for privacy."""
    return hashlib.sha256(f"{msisdn}{salt}".encode()).hexdigest()


def generate_device_fingerprint():
    """Generate a fake device fingerprint."""
    brands = ['Samsung', 'Tecno', 'Infinix', 'OPPO', 'Xiaomi', 'Nokia', 'iPhone']
    models = ['A54', 'Spark 10', 'Note 30', 'Reno 8', 'Redmi 12', 'C32', '14 Pro']
    brand = random.choice(brands)
    model = random.choice(models)
    imei = ''.join([str(random.randint(0, 9)) for _ in range(15)])
    return {
        "brand": brand,
        "model": model,
        "imei": imei,
        "fingerprint": hashlib.sha256(imei.encode()).hexdigest()[:32]
    }


def generate_subscriber(subscriber_id, fraud_profile="normal"):
    """Generate a single synthetic subscriber record."""
    mno = random.choice(list(MNO_PREFIXES.keys()))
    msisdn = generate_msisdn(mno)

    # Name
    first_name = fake.first_name()
    last_name = fake.last_name()

    # ID
    id_number = generate_id_number()

    # Location
    home_county = random.choice(KENYAN_COUNTIES)
    home_lat = random.uniform(-4.5, 1.5)
    home_lon = random.uniform(34.0, 42.0)

    # SIM swap history
    now = datetime.now()

    if fraud_profile == "sim_swap_recent":
        # SIM swapped within last 24 hours
        last_swap = now - timedelta(hours=random.randint(1, 20))
        swap_count_90d = random.randint(2, 5)
    elif fraud_profile == "sim_swap_old":
        last_swap = now - timedelta(days=random.randint(30, 80))
        swap_count_90d = 1
    elif fraud_profile == "multiple_swaps":
        last_swap = now - timedelta(days=random.randint(3, 10))
        swap_count_90d = random.randint(3, 6)
    else:
        # Normal - no recent swap
        last_swap = now - timedelta(days=random.randint(100, 500)) if random.random() > 0.3 else None
        swap_count_90d = 0

    # Device
    device = generate_device_fingerprint()

    # For fraud profiles, sometimes change the device
    if fraud_profile in ["sim_swap_recent", "multiple_swaps"] and random.random() > 0.3:
        device = generate_device_fingerprint()  # New device after swap

    return {
        "subscriber_id": subscriber_id,
        "msisdn": msisdn,
        "msisdn_hash": hash_msisdn(msisdn),
        "mno": mno,
        "id_number": id_number,
        "first_name": first_name,
        "last_name": last_name,
        "home_county": home_county,
        "home_latitude": round(home_lat, 6),
        "home_longitude": round(home_lon, 6),
        "registration_date": (now - timedelta(days=random.randint(365, 2000))).isoformat(),
        "last_sim_swap": last_swap.isoformat() if last_swap else None,
        "swap_count_90d": swap_count_90d,
        "device": device,
        "fraud_profile": fraud_profile,
        "consent_status": "active",
        "consent_granted_at": (now - timedelta(days=random.randint(30, 400))).isoformat()
    }


def generate_dataset(count=10000, fraud_ratio=0.05):
    """Generate a full synthetic dataset."""
    subscribers = []

    # Fraud profiles distribution
    profiles = ["normal"] * int(count * (1 - fraud_ratio * 3))
    profiles += ["sim_swap_recent"] * int(count * fraud_ratio)
    profiles += ["sim_swap_old"] * int(count * fraud_ratio)
    profiles += ["multiple_swaps"] * int(count * fraud_ratio)

    # Pad if needed
    while len(profiles) < count:
        profiles.append("normal")
    random.shuffle(profiles)

    for i in range(count):
        sub = generate_subscriber(f"SUB-{i+1:06d}", profiles[i])
        subscribers.append(sub)

    return subscribers


def save_dataset(subscribers, filepath="data/subscribers.json"):
    """Save dataset to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(subscribers, f, indent=2)
    print(f"Saved {len(subscribers)} synthetic subscribers to {filepath}")


def build_lookup_tables(subscribers):
    """Build hash-indexed lookup tables for fast queries."""
    by_hash = {}
    by_msisdn = {}
    by_id = {}

    for sub in subscribers:
        by_hash[sub["msisdn_hash"]] = sub
        by_msisdn[sub["msisdn"]] = sub
        by_id[sub["id_number"]] = sub

    return {
        "by_msisdn_hash": by_hash,
        "by_msisdn": by_msisdn,
        "by_id_number": by_id
    }


if __name__ == "__main__":
    print("🚀 Generating Thibitisha synthetic dataset...")
    subscribers = generate_dataset(count=10000, fraud_ratio=0.05)
    save_dataset(subscribers, "data/subscribers.json")

    # Build and save lookup tables
    lookups = build_lookup_tables(subscribers)
    with open("data/lookups.json", 'w') as f:
        # Only save hashes and IDs, not full records for the lookup file
        lookup_index = {
            "msisdn_hashes": list(lookups["by_msisdn_hash"].keys()),
            "total_subscribers": len(subscribers),
            "fraud_profiles": {
                "normal": sum(1 for s in subscribers if s["fraud_profile"] == "normal"),
                "sim_swap_recent": sum(1 for s in subscribers if s["fraud_profile"] == "sim_swap_recent"),
                "sim_swap_old": sum(1 for s in subscribers if s["fraud_profile"] == "sim_swap_old"),
                "multiple_swaps": sum(1 for s in subscribers if s["fraud_profile"] == "multiple_swaps")
            }
        }
        json.dump(lookup_index, f, indent=2)

    print(f"   Normal: {lookup_index['fraud_profiles']['normal']}")
    print(f"   Recent SIM swap: {lookup_index['fraud_profiles']['sim_swap_recent']}")
    print(f"   Old SIM swap: {lookup_index['fraud_profiles']['sim_swap_old']}")
    print(f"   Multiple swaps: {lookup_index['fraud_profiles']['multiple_swaps']}")
    print("✅ Done! Ready for development.")

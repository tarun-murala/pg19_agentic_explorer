from datasets import load_dataset

def main():
    print("Loading PG-19 parquet version from Hugging Face...")
    ds = load_dataset("emozilla/pg19")  # 👈 key change

    # Optionally pick a split
    train_ds = ds["train"]

    # Save the full dataset in HF format
    train_ds.save_to_disk("data/pg19_train_hf")

    print("Splits:", ds.keys())
    ex = train_ds[0]
    print("Title:", ex["short_book_title"])
    print("Year:", ex["publication_date"])
    print("First 300 chars:\n", ex["text"][:300])

if __name__ == "__main__":
    main()
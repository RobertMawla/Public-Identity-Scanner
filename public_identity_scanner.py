import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

from ddgs import DDGS


MAX_RESULTS_PER_QUERY = 8


SEARCH_QUERIES = [
    '"{name}"',
    '"{name}" sekolah',
    '"{name}" SMA OR SMK OR SMP',
    '"{name}" universitas OR kampus OR politeknik',
    '"{name}" mahasiswa OR student',
    '"{name}" pekerjaan OR perusahaan',
    '"{name}" developer OR programmer OR engineer',
    '"{name}" organisasi OR komunitas',
    '"{name}" lomba OR kompetisi OR prestasi',
    '"{name}" berita OR news',
    '"{name}" GitHub',
    '"{name}" LinkedIn',
]


CATEGORIES = {
    "PENDIDIKAN": [
        "sekolah",
        "school",
        "sma",
        "smk",
        "smp",
        "universitas",
        "university",
        "kampus",
        "mahasiswa",
        "mahasiswi",
        "student",
        "politeknik",
        "institut",
        "fakultas",
        "jurusan",
        "pendidikan",
        "siswa",
        "siswi",
    ],
    "PEKERJAAN": [
        "pekerjaan",
        "bekerja",
        "employee",
        "staff",
        "developer",
        "programmer",
        "engineer",
        "manager",
        "director",
        "company",
        "perusahaan",
        "startup",
        "intern",
        "internship",
        "software",
        "career",
    ],
    "ORGANISASI": [
        "organisasi",
        "organization",
        "komunitas",
        "community",
        "anggota",
        "member",
        "volunteer",
        "association",
        "himpunan",
        "ukm",
    ],
    "TEKNOLOGI": [
        "github",
        "gitlab",
        "repository",
        "programming",
        "developer",
        "software",
        "python",
        "javascript",
        "java",
        "project",
        "coding",
    ],
    "BERITA / PRESTASI": [
        "berita",
        "news",
        "juara",
        "kompetisi",
        "competition",
        "lomba",
        "prestasi",
        "award",
        "seminar",
        "event",
        "festival",
    ],
}


BLOCKED_TERMS = {
    "nik",
    "nomor kk",
    "kartu keluarga",
    "rekening",
    "password",
    "kata sandi",
    "alamat rumah",
    "nomor telepon",
    "nomor hp",
    "data bocor",
    "database bocor",
}


def banner():
    print("=" * 76)
    print("                 PUBLIC IDENTITY SCANNER")
    print("                 MULTI-SOURCE RECOVERY")
    print("=" * 76)
    print()


def clean_name(name):
    return " ".join(name.strip().split())


def validate_name(name):
    if len(name) < 3:
        return False

    if len(name.split()) < 2:
        return False

    if any(char.isdigit() for char in name):
        return False

    return True


def is_blocked(name):
    value = name.lower()

    return any(
        term in value
        for term in BLOCKED_TERMS
    )


def domain_from_url(url):
    try:
        domain = urlparse(url).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def search_query(query):
    results = []

    try:
        with DDGS() as ddgs:
            data = ddgs.text(
                query,
                max_results=MAX_RESULTS_PER_QUERY,
                safesearch="moderate",
            )

            for item in data:
                if not isinstance(item, dict):
                    continue

                title = str(
                    item.get("title", "")
                ).strip()

                url = str(
                    item.get("href", "")
                ).strip()

                body = str(
                    item.get("body", "")
                ).strip()

                if not title or not url:
                    continue

                results.append({
                    "title": title,
                    "url": url,
                    "body": body,
                    "domain": domain_from_url(url),
                    "query": query,
                })

    except Exception as error:
        print(
            f"    [!] Search error: {error}"
        )

    return results


def build_queries(name):
    return [
        query.format(name=name)
        for query in SEARCH_QUERIES
    ]


def search_all(name):
    queries = build_queries(name)

    all_results = []
    seen_urls = set()

    print("[+] Mesin pencari: DuckDuckGo")
    print("[+] Mode: otomatis")
    print()

    for number, query in enumerate(
        queries,
        start=1,
    ):
        print(
            f"[{number:02}/{len(queries):02}] "
            f"{query}"
        )

        results = search_query(query)

        for result in results:
            url_key = result["url"].lower()

            if url_key in seen_urls:
                continue

            seen_urls.add(url_key)

            all_results.append(result)

        time.sleep(0.5)

    return all_results


def relevance_score(name, result):
    target = name.lower()

    text = (
        result["title"]
        + " "
        + result["body"]
    ).lower()

    score = 0

    if target in text:
        score += 10

    for part in target.split():
        if len(part) >= 3 and part in text:
            score += 2

    return score


def classify_result(result):
    text = (
        result["title"]
        + " "
        + result["body"]
        + " "
        + result["domain"]
    ).lower()

    categories = []

    for category, keywords in CATEGORIES.items():

        if any(
            keyword.lower() in text
            for keyword in keywords
        ):
            categories.append(category)

    return categories


def analyze_results(name, results):
    analyzed = []

    for result in results:

        result["score"] = relevance_score(
            name,
            result,
        )

        result["categories"] = classify_result(
            result
        )

        analyzed.append(result)

    analyzed.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return analyzed


def group_results(results):
    groups = defaultdict(list)

    for result in results:

        for category in result["categories"]:

            if result not in groups[category]:
                groups[category].append(result)

    return groups


def print_top_results(results):
    print()
    print("=" * 76)
    print("HASIL PUBLIK TERKAIT")
    print("=" * 76)

    if not results:
        print("\nTidak ada hasil yang berhasil diperoleh.")
        return

    for index, result in enumerate(
        results[:20],
        start=1,
    ):
        print()
        print(
            f"{index}. {result['title']}"
        )
        print(
            f"   Situs   : {result['domain']}"
        )

        if result["body"]:
            body = re.sub(
                r"\s+",
                " ",
                result["body"],
            )

            print(
                f"   Informasi: {body[:350]}"
            )

        print(
            f"   URL     : {result['url']}"
        )


def print_categories(results):
    groups = group_results(results)

    print()
    print("=" * 76)
    print("INFORMASI TERKELOMPOK")
    print("=" * 76)

    if not groups:
        print(
            "\nBelum ditemukan konteks yang cukup."
        )
        return

    category_order = [
        "PENDIDIKAN",
        "PEKERJAAN",
        "ORGANISASI",
        "TEKNOLOGI",
        "BERITA / PRESTASI",
    ]

    for category in category_order:

        items = groups.get(
            category,
            [],
        )

        if not items:
            continue

        print()
        print(f"[{category}]")

        displayed = set()

        for item in items:

            identity = (
                item["title"].strip()
            )

            if identity in displayed:
                continue

            displayed.add(identity)

            print(
                f"  - {identity}"
            )

            if item["body"]:
                body = re.sub(
                    r"\s+",
                    " ",
                    item["body"],
                )

                print(
                    f"    {body[:250]}"
                )

            print(
                f"    Sumber: {item['domain']}"
            )

            if len(displayed) >= 5:
                break


def make_conclusion(name, results):
    groups = group_results(results)

    print()
    print("=" * 76)
    print("KESIMPULAN")
    print("=" * 76)

    print()
    print(f"Nama pencarian : {name}")
    print(
        f"Hasil unik     : {len(results)}"
    )
    print(
        f"Waktu          : "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print()

    detected = []

    for category in [
        "PENDIDIKAN",
        "PEKERJAAN",
        "ORGANISASI",
        "TEKNOLOGI",
        "BERITA / PRESTASI",
    ]:
        if groups.get(category):
            detected.append(category)

    if not results:

        print(
            "Tidak ditemukan hasil publik yang dapat "
            "dianalisis."
        )

        return

    if detected:

        print(
            "Jejak publik yang terdeteksi:"
        )

        for category in detected:
            print(
                f"  [+] {category}: "
                f"{len(groups[category])} hasil"
            )

    else:

        print(
            "Nama ditemukan pada web, tetapi konteks "
            "hasil belum cukup untuk mengelompokkannya."
        )

    print()
    print(
        "Interpretasi:"
    )

    if groups.get("PENDIDIKAN"):
        print(
            "- Terdapat hasil publik yang memiliki "
            "konteks pendidikan."
        )

    if groups.get("PEKERJAAN"):
        print(
            "- Terdapat hasil publik yang memiliki "
            "konteks pekerjaan."
        )

    if groups.get("ORGANISASI"):
        print(
            "- Terdapat hasil publik yang memiliki "
            "konteks organisasi atau komunitas."
        )

    if groups.get("TEKNOLOGI"):
        print(
            "- Terdapat hasil publik yang memiliki "
            "konteks teknologi atau proyek."
        )

    if groups.get("BERITA / PRESTASI"):
        print(
            "- Terdapat hasil publik yang memiliki "
            "konteks berita, kegiatan, atau prestasi."
        )

    print()
    print(
        "Catatan: hasil dengan nama yang sama tidak "
        "otomatis berarti berasal dari orang yang sama."
    )


def save_report(name, results):
    safe_name = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        name,
    )

    filename = (
        f"recovery_{safe_name}.txt"
    )

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "PUBLIC IDENTITY SCANNER\n"
        )

        file.write(
            "=" * 70 + "\n"
        )

        file.write(
            f"Target: {name}\n"
        )

        file.write(
            f"Time: "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        for index, result in enumerate(
            results,
            start=1,
        ):

            file.write(
                f"[{index}] "
                f"{result['title']}\n"
            )

            file.write(
                f"Domain: "
                f"{result['domain']}\n"
            )

            file.write(
                f"URL: "
                f"{result['url']}\n"
            )

            file.write(
                f"Kategori: "
                f"{', '.join(result['categories'])}\n"
            )

            file.write(
                f"Info: "
                f"{result['body']}\n"
            )

            file.write(
                f"Score: "
                f"{result['score']}\n\n"
            )

    return filename


def main():
    banner()

    name = input(
        "Masukkan nama lengkap: "
    )

    name = clean_name(name)

    if not validate_name(name):
        print()
        print(
            "[ERROR] Masukkan nama lengkap yang valid."
        )
        sys.exit(1)

    if is_blocked(name):
        print()
        print(
            "[ERROR] Input tidak didukung."
        )
        sys.exit(1)

    print()
    print(
        f"[+] Target: {name}"
    )

    print(
        "[+] Browser tidak dibuka."
    )

    print(
        "[+] Pencarian berjalan otomatis."
    )

    print()

    raw_results = search_all(name)

    results = analyze_results(
        name,
        raw_results,
    )

    print_top_results(results)

    print_categories(results)

    make_conclusion(
        name,
        results,
    )

    filename = save_report(
        name,
        results,
    )

    print()
    print("=" * 76)
    print(
        f"[+] Recovery report: {filename}"
    )
    print("=" * 76)


if __name__ == "__main__":
    main()
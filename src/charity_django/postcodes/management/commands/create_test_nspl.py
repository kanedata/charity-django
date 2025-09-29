import csv
import random
import zipfile
from collections import Counter, defaultdict
from io import TextIOWrapper

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """Create a test NSPL file from a real one."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            help="Path to the output file",
        )
        parser.add_argument(
            "inputfile",
            type=str,
            help="Path to the input file",
        )
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        # open the input zip file
        input_path = options["inputfile"]
        output_path = options["output"]
        if not output_path:
            output_path = input_path.replace(".zip", "_TEST.zip")

        with (
            zipfile.ZipFile(input_path, "r") as input_zip,
            zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as output_zip,
        ):
            multi_csv_files = defaultdict(list)
            other_data_files = []
            for item in input_zip.infolist():
                if item.filename.startswith(
                    "Data/multi_csv/"
                ) and item.filename.endswith(".csv"):
                    # open the file and look for the country codes
                    with input_zip.open(item) as f:
                        reader = csv.DictReader(TextIOWrapper(f, encoding="utf-8"))
                        country_column = next(
                            (
                                c
                                for c in reader.fieldnames
                                if c.lower().startswith("ctry")
                            ),
                            None,
                        )
                        countries = set()
                        for row in reader:
                            if row[country_column]:
                                countries.add(row[country_column])

                        if len(countries) == 0:
                            print(
                                f"Found multi_csv file with no countries: {item.filename}"
                            )
                            continue
                        elif len(countries) > 1:
                            print(
                                f"Found multi_csv file with multiple countries {countries}: {item.filename}"
                            )
                            country_to_use = "multiple"
                        else:
                            country_to_use = countries.pop()

                        print(
                            f"Found multi_csv file [{country_to_use}]: {item.filename}"
                        )
                        multi_csv_files[country_to_use].append(item)
                elif item.filename.startswith("Data/"):
                    # skip other data files
                    if item.filename.endswith(".csv") or item.filename.endswith(".txt"):
                        other_data_files.append(item)
                    print(f"Skipping data file: {item.filename}")
                    continue
                else:
                    # copy other files unchanged
                    print(f"Copying {item.filename}")
                    output_zip.writestr(item, input_zip.read(item.filename))

            # we only take 10 multi_csv files
            print([(k, len(v)) for k, v in multi_csv_files.items()])

            files_to_use = []
            # one from each country
            for country, items in multi_csv_files.items():
                files_to_use.extend(random.sample(items, 1))

            remaining = 10 - len(files_to_use)
            if remaining > 0:
                all_items = [
                    item
                    for sublist in multi_csv_files.values()
                    for item in sublist
                    if item not in files_to_use
                ]
                files_to_use.extend(random.sample(all_items, remaining))

            postcodes = set()
            for item in files_to_use:
                # we take the first line (the header) and then 200 random lines
                with input_zip.open(item) as f:
                    lines = f.readlines()
                    header = lines[0]
                    data_lines = random.sample(lines[1:], 200)
                    print(f"Copying 200 rows from {item.filename}")
                    output_zip.writestr(item, header + b"".join(data_lines))

                    for line in data_lines:
                        postcode = line.decode("utf-8").split(",")[0]
                        if postcode:
                            postcodes.add(postcode)

            print(f"Total postcodes in test file: {len(postcodes):,}")

            # go through the other data files and copy only those rows with postcodes we have
            all_file_csv = None
            for item in other_data_files:
                with input_zip.open(item) as f:
                    print(f"Processing {item.filename}")
                    lines_to_write = []
                    if item.filename.endswith(".csv"):
                        all_file_csv = item
                        # first line is the header
                        lines_to_write.append(f.readline())
                        for line in f.readlines():
                            if line.decode("utf-8").split(",")[0] in postcodes:
                                lines_to_write.append(line)

                    if item.filename.endswith(".txt"):
                        for line in f.readlines():
                            if '"' + line[0:7].decode("utf-8") + '"' in postcodes:
                                lines_to_write.append(line)
                    print(f"Copying {len(lines_to_write)} rows from {item.filename}")
                    output_zip.writestr(item, b"".join(lines_to_write))

            # Extract some needed statistics for the test data
            with output_zip.open(all_file_csv) as f:
                reader = csv.DictReader(TextIOWrapper(f, encoding="utf-8"))
                la_codes = Counter()
                user_types = Counter()
                imd_values = Counter()
                for row in reader:
                    la_codes[row["lad25cd"]] += 1
                    user_types[row["usrtypind"]] += 1
                    if row["imd20ind"]:
                        imd_values[int(row["imd20ind"])] += 1

            print("Local Authority Codes:")
            for k, v in la_codes.most_common(3):
                print(f"  {k}: {v}")
            print("User Types:")
            for k, v in user_types.most_common(3):
                print(f"  {k}: {v}")
            print("IMD values:")
            for k, v in imd_values.most_common(3):
                print(f"  {k}: {v}")
        print(f"Wrote test file to {output_path}")

import os
import json
import logging
import pandas as pd
from openpyxl import load_workbook

logging.basicConfig(level=logging.INFO)

def read_mapping(file_path):
    """Reads the mapping from an Excel file and returns a dictionary."""
    mapping = {}
    workbook = load_workbook(filename=file_path)
    sheet = workbook.active
    for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip header row
        if row[0] and row[1]:
            mapping[row[0]] = row[1]
    return mapping

def find_node_value(json_node, keys, level=0):
    """Recursively fetches a value from a nested JSON object using a list of keys."""
    if level >= len(keys):
        return json_node if isinstance(json_node, str) else None
    key = keys[level]
    if isinstance(json_node, dict) and key in json_node:
        return find_node_value(json_node[key], keys, level + 1)
    elif isinstance(json_node, list) and key.isdigit():
        index = int(key)
        return find_node_value(json_node[index], keys, level + 1) if index < len(json_node) else None
    return None

def compare_using_mapping(legacy_record, payer_record, mapping):
    """Compares two JSON objects based on the provided mapping."""
    matched_count = 0
    total_keys = len(mapping)
    payer_value = None
    
    for old_key, new_key in mapping.items():
        old_value = find_node_value(legacy_record, old_key.split('/'))
        new_value = find_node_value(payer_record, new_key.split('/'))
        if old_value and old_value == new_value:
            matched_count += 1
            if new_key == "claimIdentifiers/patientAccountNumber":
                payer_value = old_value
    
    status_code = "MATCHED" if matched_count == total_keys else f"PARTIAL_MATCH ({matched_count}/{total_keys})"
    return {"Length": total_keys, "StatusCode": status_code, "Payer": payer_value}

def process_json_files(mapping_file, legacy_file, payer_file):
    """Processes JSON files and logs the matched records."""
    mapping = read_mapping(mapping_file)
    with open(legacy_file, 'r', encoding='utf-8') as lf, open(payer_file, 'r', encoding='utf-8') as pf:
        legacy_response = json.load(lf)
        payer_response = json.load(pf)
    
    legacy_array = legacy_response.get("searchResult", {}).get("searchOutput", {}).get("claims", [])
    payer_array = payer_response.get("data", [])
    
    for legacy_record in legacy_array:
        for payer_record in payer_array:
            status = compare_using_mapping(legacy_record, payer_record, mapping)
            if status["StatusCode"] == "MATCHED":
                logging.info(f"Match found: {json.dumps(legacy_record)} with {json.dumps(payer_record)}")
    
if __name__ == "__main__":
    MAPPING_FILE = "C:/Users/nezam/eclipse-workspace/Canocial/src/main/java/Data/mappingForFilteringFiles.xlsx"
    LEGACY_FILE = "C:/Users/nezam/eclipse-workspace/Canocial/src/main/java/Data/response1.json"
    PAYER_FILE = "C:/Users/nezam/eclipse-workspace/Canocial/src/main/java/Data/response2.json"
    
    process_json_files(MAPPING_FILE, LEGACY_FILE, PAYER_FILE)

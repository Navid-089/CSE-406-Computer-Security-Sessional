#!/usr/bin/env python3
"""
Dataset Merger Script

This script merges all dataset.json files from subfolders in the data directory,
performs validation checks, reassigns website indices, and adds metadata and source information.
"""

import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Any, Tuple


def load_json_file(filepath: str) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except Exception as e:
        raise Exception(f"Error reading {filepath}: {e}")


def validate_dataset_structure(data: List[Dict], source_folder: str) -> Tuple[bool, str]:
    """
    Validate the structure of a dataset.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, list):
        return False, f"Dataset in {source_folder} is not an array"
    
    if not data:
        return False, f"Dataset in {source_folder} is empty"
    
    trace_data_length = None
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            return False, f"Item {i} in {source_folder} is not a JSON object"
        
        # Check required fields
        if 'website' not in item:
            return False, f"Item {i} in {source_folder} missing 'website' field"
        
        if 'trace_data' not in item:
            return False, f"Item {i} in {source_folder} missing 'trace_data' field"
        
        # Check field types
        if not isinstance(item['website'], str):
            return False, f"Item {i} in {source_folder} has non-string 'website' field"
        
        if not isinstance(item['trace_data'], list):
            return False, f"Item {i} in {source_folder} has non-array 'trace_data' field"
        
        # Check if all trace_data elements are numbers
        for j, trace_val in enumerate(item['trace_data']):
            if not isinstance(trace_val, (int, float)):
                return False, f"Item {i} in {source_folder} has non-numeric value at trace_data[{j}]"
        
        # Check trace_data length consistency
        current_length = len(item['trace_data'])
        if trace_data_length is None:
            trace_data_length = current_length
        elif trace_data_length != current_length:
            return False, f"Item {i} in {source_folder} has trace_data length {current_length}, expected {trace_data_length}"
    
    return True, ""


def validate_cross_dataset_consistency(all_datasets: Dict[str, List[Dict]]) -> Tuple[bool, str]:
    """
    Validate that all datasets have the same trace_data length across all files.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    expected_length = None
    
    for source_folder, data in all_datasets.items():
        if data:  # Skip empty datasets
            current_length = len(data[0]['trace_data'])
            if expected_length is None:
                expected_length = current_length
            elif expected_length != current_length:
                return False, f"Dataset {source_folder} has trace_data length {current_length}, but other datasets have length {expected_length}"
    
    return True, ""


def collect_unique_websites(all_datasets: Dict[str, List[Dict]]) -> Dict[str, int]:
    """
    Collect all unique websites and assign them new indices.
    
    Returns:
        Dictionary mapping website URL to new index
    """
    unique_websites = set()
    
    for data in all_datasets.values():
        for item in data:
            unique_websites.add(item['website'])
    
    # Sort websites for consistent ordering
    sorted_websites = sorted(unique_websites)
    
    # Create mapping from website to index
    website_to_index = {website: idx for idx, website in enumerate(sorted_websites)}
    
    return website_to_index


def merge_datasets(data_folder: str = "offline-2-datasets-security") -> None:
    """
    Main function to merge all datasets.
    """
    print("🔍 Scanning data folder...")
    
    if not os.path.exists(data_folder):
        print(f"\n\n❌❌❌ Error: Data folder '{data_folder}' not found\n\n")
        sys.exit(1)
    
    # Find all subfolders
    subfolders = [item for item in os.listdir(data_folder) 
                  if os.path.isdir(os.path.join(data_folder, item))]
    
    if not subfolders:
        print(f"\n\n❌❌❌ Error: No subfolders found in '{data_folder}'\n\n")
        sys.exit(1)
    
    print(f"📁 Found {len(subfolders)} subfolders: {', '.join(subfolders)}")
    
    all_datasets = {}
    all_metadata = {}
    
    # Load and validate each dataset
    print("\n📊 Loading and validating datasets...")
    
    for subfolder in subfolders:
        subfolder_path = os.path.join(data_folder, subfolder)
        dataset_path = os.path.join(subfolder_path, "dataset_normalised.json")
        
        
        print(f"  Processing {subfolder}...")
        
        # Check if files exist
        if not os.path.exists(dataset_path):
            print(f"\n\n❌❌❌ Error: dataset.json not found in {subfolder}\n\n")
            sys.exit(1)
        
        # if not os.path.exists(metadata_path):
        #     print(f"\n\n❌❌❌ Error: metadata.json not found in {subfolder}\n\n")
        #     sys.exit(1)
        
        try:
            # Load dataset
            dataset = load_json_file(dataset_path)
            
            # # Load metadata
            # metadata = load_json_file(metadata_path)
            
            # Validate dataset structure
            is_valid, error_msg = validate_dataset_structure(dataset, subfolder)
            if not is_valid:
                print(f"\n\n❌❌❌ Validation Error: {error_msg}\n\n")
                sys.exit(1)
            
            all_datasets[subfolder] = dataset
            # all_metadata[subfolder] = metadata
            
            print(f"    ✅ {len(dataset)} items loaded successfully")
            
        except Exception as e:
            print(f"\n\n❌❌❌ Error processing {subfolder}: {e}\n\n")
            sys.exit(1)
    
    # Validate cross-dataset consistency
    print("\n🔍 Validating cross-dataset consistency...")
    is_valid, error_msg = validate_cross_dataset_consistency(all_datasets)
    if not is_valid:
        print(f"\n\n❌❌❌ Consistency Error: {error_msg}\n\n")
        sys.exit(1)
    
    print("✅ All datasets are consistent")
    
    # Collect unique websites and create new mapping
    print("\n🌐 Collecting unique websites...")
    website_to_index = collect_unique_websites(all_datasets)
    
    print(f"Found {len(website_to_index)} unique websites:")
    for website, idx in sorted(website_to_index.items(), key=lambda x: x[1]):
        print(f"  {idx}: {website}")
    
    # Merge all datasets
    print("\n🔄 Merging datasets...")
    merged_dataset = []
    
    for source_folder, dataset in all_datasets.items():
        # metadata = all_metadata[source_folder]
        
        for item in dataset:
            # Create merged item
            merged_item = {
                "website": item["website"],
                "website_index": website_to_index[item["website"]],
                "trace_data": item["trace_data"],
                # "metadata": metadata,
                # "source": source_folder
            }
            
            merged_dataset.append(merged_item)
    
    print(f"✅ Merged {len(merged_dataset)} total items from {len(all_datasets)} sources")
    
    # Write merged dataset
    output_path = "dataset_normalised.json"
    print(f"\n💾 Writing merged dataset to {output_path}...")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_dataset, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully created {output_path}")
        print(f"📈 Final dataset contains {len(merged_dataset)} items")
        print(f"🌐 Covering {len(website_to_index)} unique websites")
        
        # Print summary statistics
        source_counts = defaultdict(int)
        website_counts = defaultdict(int)
        
        for item in merged_dataset:
            source_counts[item['source']] += 1
            website_counts[item['website']] += 1
        
        print("\n📊 Summary by source:")
        for source, count in sorted(source_counts.items()):
            print(f"  {source}: {count} items")
        
        print("\n🌐 Summary by website:")
        for website, count in sorted(website_counts.items(), key=lambda x: website_to_index[x[0]]):
            website_idx = website_to_index[website]
            print(f"  [{website_idx}] {website}: {count} items")
            
    except Exception as e:
        print(f"\n\n❌❌❌ Error writing output file: {e}\n\n")
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 Dataset Merger Starting...")
    merge_datasets()
    print("\n🎉 Dataset merger completed successfully!")

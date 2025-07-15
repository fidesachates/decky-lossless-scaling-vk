"""
Constants for the lsfg-vk plugin.
"""

from pathlib import Path

# Directory paths
LOCAL_LIB = ".local/lib"
LOCAL_SHARE_BASE = ".local/share"
VULKAN_LAYER_DIR = ".local/share/vulkan/implicit_layer.d"

# File names
SCRIPT_NAME = "lsfg"
FLATPAK_SCRIPT_NAME = "lsfg-flatpak"
LIB_FILENAME = "liblsfg-vk.so"
JSON_FILENAME = "VkLayer_LS_frame_generation.json"
ZIP_FILENAME = "lsfg-vk_archlinux.zip"

# File extensions
SO_EXT = ".so"
JSON_EXT = ".json"

# Directory for the zip file
BIN_DIR = "bin"

# Lossless Scaling paths
STEAM_COMMON_PATH = Path("steamapps/common/Lossless Scaling")
LOSSLESS_DLL_NAME = "Lossless.dll"

# Script template
LSFG_SCRIPT_TEMPLATE = """#!/bin/bash

{enable_lsfg}
export LSFG_MULTIPLIER={multiplier}
export LSFG_FLOW_SCALE={flow_scale}
{hdr}
{perf_mode}
{immediate_mode}

# Execute the passed command with the environment variables set
exec "$@"
"""

# Flatpak script template
LSFG_FLATPAK_SCRIPT_TEMPLATE = """#!/bin/bash

# LSFG Flatpak Sync Script
# This script synchronizes LSFG files between host and flatpak environments
# Usage: Add this script to your Steam launch options for flatpak games

set -e

# Paths
HOST_LIB_DIR="$HOME/.local/lib"
HOST_SHARE_DIR="$HOME/.local/share/vulkan/implicit_layer.d"

# File names
LIB_FILE="liblsfg-vk.so"
JSON_FILE="VkLayer_LS_frame_generation.json"

# Function to calculate SHA256 checksum
get_sha256() {
    if [[ -f "$1" ]]; then
        sha256sum "$1" | cut -d' ' -f1
    else
        echo ""
    fi
}

# Function to copy file if source exists
safe_copy() {
    local src="$1"
    local dst="$2"
    
    if [[ -f "$src" ]]; then
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        echo "Copied $src to $dst"
        return 0
    else
        echo "Warning: Source file $src does not exist"
        return 1
    fi
}

# Function to sync LSFG files
sync_lsfg_files() {
    local app_id="$1"
    
    # Update paths with actual app ID
    local flatpak_lib_dir="$HOME/.var/app/$app_id/.local/lib"
    local flatpak_share_dir="$HOME/.var/app/$app_id/.local/share/vulkan/implicit_layer.d"
    
    echo "Syncing LSFG files for flatpak app: $app_id"
    
    # Create flatpak directories if they don't exist
    mkdir -p "$flatpak_lib_dir"
    mkdir -p "$flatpak_share_dir"
    
    # Sync library file
    local host_lib="$HOST_LIB_DIR/$LIB_FILE"
    local flatpak_lib="$flatpak_lib_dir/$LIB_FILE"
    
    if [[ -f "$host_lib" ]]; then
        local host_lib_sha=$(get_sha256 "$host_lib")
        local flatpak_lib_sha=$(get_sha256 "$flatpak_lib")
        
        if [[ "$host_lib_sha" != "$flatpak_lib_sha" ]]; then
            safe_copy "$host_lib" "$flatpak_lib"
        else
            echo "Library file is up to date"
        fi
    else
        echo "Warning: Host library file not found at $host_lib"
    fi
    
    # Sync JSON file
    local host_json="$HOST_SHARE_DIR/$JSON_FILE"
    local flatpak_json="$flatpak_share_dir/$JSON_FILE"
    
    if [[ -f "$host_json" ]]; then
        local host_json_sha=$(get_sha256 "$host_json")
        local flatpak_json_sha=$(get_sha256 "$flatpak_json")
        
        if [[ "$host_json_sha" != "$flatpak_json_sha" ]]; then
            safe_copy "$host_json" "$flatpak_json"
        else
            echo "JSON file is up to date"
        fi
    else
        echo "Warning: Host JSON file not found at $host_json"
    fi
}

# Function to detect flatpak app ID
detect_app_id() {
    # Try to detect from common flatpak app IDs
    local common_ids=("com.valvesoftware.Steam" "org.prismlauncher.PrismLauncher" "net.lutris.Lutris" "com.heroicgameslauncher.hgl")
    
    for app_id in "${{common_ids[@]}}"; do
        if [[ -d "$HOME/.var/app/$app_id" ]]; then
            echo "$app_id"
            return 0
        fi
    done
    
    return 1
}

# Function to validate app ID format
is_valid_app_id() {
    local app_id="$1"
    # Check if it looks like a flatpak app ID (at least two dots)
    if [[ "$app_id" =~ ^[a-zA-Z0-9_.-]+\\.[a-zA-Z0-9_.-]+\\.[a-zA-Z0-9_.-]+.*$ ]]; then
        return 0
    else
        return 1
    fi
}

# Main execution
main() {
    # Check if we have arguments (the original command to execute)
    if [[ $# -eq 0 ]]; then
        echo "Usage: $0 [flatpak_app_id] [command...]"
        echo "Example: $0 com.valvesoftware.Steam %command%"
        echo "If no app_id is provided, the script will try to auto-detect it."
        exit 1
    fi
    
    local app_id=""
    
    # Check if first argument looks like a flatpak app ID
    if is_valid_app_id "$1"; then
        app_id="$1"
        shift  # Remove app_id from arguments
        echo "Using provided flatpak app ID: $app_id"
    else
        # Try to auto-detect app ID
        if app_id=$(detect_app_id); then
            echo "Auto-detected flatpak app ID: $app_id"
        else
            echo "Could not detect flatpak app ID and none was provided."
            echo "Usage: $0 [flatpak_app_id] [command...]"
            echo "Available flatpak apps:"
            if ls "$HOME/.var/app/" 2>/dev/null; then
                ls "$HOME/.var/app/"
            else
                echo "No flatpak apps found"
            fi
            exit 1
        fi
    fi
    
    # Verify the app directory exists
    if [[ ! -d "$HOME/.var/app/$app_id" ]]; then
        echo "Error: Flatpak app directory not found: $HOME/.var/app/$app_id"
        exit 1
    fi
    
    # Sync LSFG files
    sync_lsfg_files "$app_id"
    
    echo "LSFG sync complete. Executing original command..."
    
    # Execute the original command
    exec "$@"
}

# Run main function with all arguments
main "$@"
"""

# Environment variable names
ENV_LSFG_DLL_PATH = "LSFG_DLL_PATH"
ENV_XDG_DATA_HOME = "XDG_DATA_HOME"
ENV_HOME = "HOME"

# Default configuration values
DEFAULT_MULTIPLIER = 2
DEFAULT_FLOW_SCALE = 1.0
DEFAULT_ENABLE_LSFG = True
DEFAULT_HDR = False
DEFAULT_PERF_MODE = False
DEFAULT_IMMEDIATE_MODE = False

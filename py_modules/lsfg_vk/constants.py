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
# 
# Usage in Steam Launch Options:
# Replace the Target field with this script path and adjust launch options:
# Target: /home/deck/lsfg-flatpak
# Launch Options: run com.valvesoftware.Steam %command%
#
# Or for non-Steam flatpak shortcuts:
# ~/lsfg-flatpak com.app.id

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

# Function to detect flatpak app ID from arguments or common locations
detect_app_id() {
    # Check for common flatpak app IDs in arguments
    for arg in "$@"; do
        case "$arg" in
            com.*|org.*|net.*|io.*|app.*)
                if [[ "$arg" =~ ^[a-zA-Z0-9_.-]+\\.[a-zA-Z0-9_.-]+\\.[a-zA-Z0-9_.-]+.*$ ]]; then
                    echo "$arg"
                    return 0
                fi
                ;;
        esac
    done
    
    # Try to detect from common flatpak app IDs in filesystem
    local common_ids=("com.valvesoftware.Steam" "org.prismlauncher.PrismLauncher" "net.lutris.Lutris" "com.heroicgameslauncher.hgl" "com.moonlight_stream.Moonlight")
    
    for app_id in "${common_ids[@]}"; do
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
    local app_id=""
    local flatpak_args=()
    
    # Parse arguments to find app ID and construct flatpak command
    if [[ $# -eq 0 ]]; then
        echo "LSFG Flatpak Sync Script"
        echo "Usage: $0 [run] <app_id> [additional_args...]"
        echo "Example: $0 run com.valvesoftware.Steam"
        echo "Example: $0 com.valvesoftware.Steam"
        exit 1
    fi
    
    # Handle different argument patterns
    if [[ "$1" == "run" ]]; then
        # Pattern: ~/lsfg-flatpak run com.app.id [args...]
        shift
        if [[ $# -gt 0 ]] && is_valid_app_id "$1"; then
            app_id="$1"
            shift
            flatpak_args=("run" "$app_id" "$@")
        else
            echo "Error: 'run' command requires a valid flatpak app ID"
            if [[ $# -gt 0 ]]; then
                echo "Provided argument '$1' is not a valid flatpak app ID"
            fi
            exit 1
        fi
    elif is_valid_app_id "$1"; then
        # Pattern: ~/lsfg-flatpak com.app.id [args...]
        app_id="$1"
        shift
        flatpak_args=("run" "$app_id" "$@")
    else
        # Try to detect app ID from all arguments
        if app_id=$(detect_app_id "$@"); then
            echo "Auto-detected flatpak app ID: $app_id"
            # Remove the detected app_id from arguments and construct flatpak command
            local new_args=()
            local found_app_id=false
            for arg in "$@"; do
                if [[ "$arg" == "$app_id" ]]; then
                    found_app_id=true
                elif [[ "$arg" == "run" ]] && [[ "$found_app_id" == false ]]; then
                    # Keep 'run' if it comes before the app_id
                    new_args+=("$arg")
                else
                    new_args+=("$arg")
                fi
            done
            
            # Construct flatpak command
            if [[ "${new_args[0]}" == "run" ]]; then
                flatpak_args=("run" "$app_id" "${new_args[@]:1}")
            else
                flatpak_args=("run" "$app_id" "${new_args[@]}")
            fi
        else
            echo "Could not detect flatpak app ID from arguments: $*"
            echo "Available flatpak apps:"
            if ls "$HOME/.var/app/" 2>/dev/null | head -10; then
                echo "..."
            else
                echo "No flatpak apps found"
            fi
            exit 1
        fi
    fi
    
    # Verify the app directory exists (or create path for it)
    if [[ ! -d "$HOME/.var/app/$app_id" ]]; then
        echo "Warning: Flatpak app directory not found: $HOME/.var/app/$app_id"
        echo "This may be normal if the app hasn't been run yet."
    fi
    
    # Sync LSFG files
    sync_lsfg_files "$app_id"
    
    echo "LSFG sync complete. Setting up LSFG environment variables..."
    
    # Try to source environment variables from the regular lsfg script if it exists
    if [[ -f "$HOME/lsfg" ]]; then
        echo "Loading LSFG configuration from ~/lsfg script..."
        # Extract export statements from the lsfg script
        source <(grep "^export " "$HOME/lsfg" 2>/dev/null || true)
    else
        echo "Using default LSFG configuration..."
        # Set up default LSFG environment variables
        export ENABLE_LSFG=1
        export LSFG_MULTIPLIER=2
        export LSFG_FLOW_SCALE=1.0
        # export LSFG_HDR=1
        # export LSFG_PERF_MODE=1
        # export MESA_VK_WSI_PRESENT_MODE=immediate # - disable vsync
    fi
    
    # Show which LSFG settings are active
    echo "Active LSFG settings:"
    [[ -n "$ENABLE_LSFG" ]] && echo "  ENABLE_LSFG=$ENABLE_LSFG"
    [[ -n "$LSFG_MULTIPLIER" ]] && echo "  LSFG_MULTIPLIER=$LSFG_MULTIPLIER"
    [[ -n "$LSFG_FLOW_SCALE" ]] && echo "  LSFG_FLOW_SCALE=$LSFG_FLOW_SCALE"
    [[ -n "$LSFG_HDR" ]] && echo "  LSFG_HDR=$LSFG_HDR"
    [[ -n "$LSFG_PERF_MODE" ]] && echo "  LSFG_PERF_MODE=$LSFG_PERF_MODE"
    [[ -n "$MESA_VK_WSI_PRESENT_MODE" ]] && echo "  MESA_VK_WSI_PRESENT_MODE=$MESA_VK_WSI_PRESENT_MODE"
    
    echo "Executing flatpak command: flatpak ${flatpak_args[*]}"
    
    # Execute flatpak with the constructed arguments
    exec /usr/bin/flatpak "${flatpak_args[@]}"
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

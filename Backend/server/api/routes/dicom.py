"""DICOM processing routes for MedCompanion server."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pydicom
from pathlib import Path
from PIL import Image
import numpy as np
import json
import uuid
import tempfile
from typing import Dict, Any, List

router = APIRouter(prefix="/api/v1/dicom", tags=["dicom"])

# Store active temp folders for cleanup on shutdown
active_temp_folders = []


class ProcessSeriesRequest(BaseModel):
    folder: str


class ProcessSeriesResponse(BaseModel):
    success: bool
    output_folder: str
    total_slices: int
    series_info_file: str


@router.post("/process-series", response_model=ProcessSeriesResponse)
async def process_dicom_series(request: ProcessSeriesRequest):
    """
    Process all DICOM files in a folder and generate PNGs with metadata.
    Outputs to a temporary folder that persists until server shutdown.
    """
    try:
        folder_path = Path(request.folder)
        
        # Validate folder exists
        if not folder_path.exists() or not folder_path.is_dir():
            raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder}")
        
        # Find all DICOM files
        dicom_files = sorted([
            f for f in folder_path.iterdir()
            if f.suffix.lower() in ['.dcm', '.dicom', '.DCM', '.DICOM']
        ])
        
        if not dicom_files:
            raise HTTPException(status_code=404, detail="No DICOM files found in folder")
        
        # Create temp folder inside the DICOM folder
        output_folder = folder_path / ".medcompanion-temp"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Track for cleanup
        active_temp_folders.append(str(output_folder))
        
        # Process first file to get series-level metadata
        series_metadata = None
        
        # Process all DICOM files
        processed_count = 0
        
        for idx, dcm_file in enumerate(dicom_files):
            try:
                # Read DICOM
                ds = pydicom.dcmread(str(dcm_file))
                
                # Extract series metadata from first file
                if series_metadata is None:
                    series_metadata = extract_series_metadata(ds, len(dicom_files))
                
                # Get pixel data
                pixel_array = ds.pixel_array
                
                # Normalize to 0-255
                pixel_normalized = normalize_pixels(pixel_array)
                
                # Convert to PIL Image and save as PNG
                img = Image.fromarray(pixel_normalized)
                png_filename = f"slice-{idx:04d}.png"
                img.save(output_folder / png_filename, format='PNG')
                
                # Extract slice-specific metadata
                slice_metadata = extract_slice_metadata(ds, idx, dcm_file.name)
                
                # Save slice metadata as JSON
                json_filename = f"slice-{idx:04d}.json"
                with open(output_folder / json_filename, 'w') as f:
                    json.dump(slice_metadata, f, indent=2)
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {dcm_file.name}: {e}")
                continue
        
        if processed_count == 0:
            raise HTTPException(status_code=500, detail="Failed to process any DICOM files")
        
        # Save series info
        series_info_path = output_folder / "series-info.json"
        with open(series_info_path, 'w') as f:
            json.dump(series_metadata, f, indent=2)
        
        return ProcessSeriesResponse(
            success=True,
            output_folder=str(output_folder),
            total_slices=processed_count,
            series_info_file="series-info.json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


def normalize_pixels(pixel_array: np.ndarray) -> np.ndarray:
    """
    Normalize pixel values to 0-255 range for PNG output.
    Handles different DICOM pixel value ranges.
    """
    pixel_array = pixel_array.astype(float)
    pixel_min = pixel_array.min()
    pixel_max = pixel_array.max()
    
    if pixel_max > pixel_min:
        normalized = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255)
    else:
        normalized = np.zeros_like(pixel_array)
    
    return normalized.astype(np.uint8)


def extract_series_metadata(ds: pydicom.Dataset, total_slices: int) -> Dict[str, Any]:
    """
    Extract series-level metadata that applies to all slices.
    Based on actual DICOM tags found in sample MRI file (0002.DCM).
    """
    return {
        # Patient Information
        "patient_name": safe_get_tag(ds, 'PatientName', 'Unknown'),
        "patient_id": safe_get_tag(ds, 'PatientID', 'Unknown'),
        "patient_sex": safe_get_tag(ds, 'PatientSex', ''),
        "patient_age": safe_get_tag(ds, 'PatientAge', ''),
        "patient_size": safe_get_tag(ds, 'PatientSize', ''),  # Height in meters
        "patient_weight": safe_get_tag(ds, 'PatientWeight', ''),  # Weight in kg
        
        # Study Information
        "study_date": safe_get_tag(ds, 'StudyDate', 'Unknown'),
        "study_time": safe_get_tag(ds, 'StudyTime', ''),
        "study_description": safe_get_tag(ds, 'StudyDescription', ''),
        "study_instance_uid": safe_get_tag(ds, 'StudyInstanceUID', ''),
        "accession_number": safe_get_tag(ds, 'AccessionNumber', ''),
        
        # Series Information
        "series_description": safe_get_tag(ds, 'SeriesDescription', ''),
        "series_number": safe_get_tag(ds, 'SeriesNumber', ''),
        "series_date": safe_get_tag(ds, 'SeriesDate', ''),
        "series_time": safe_get_tag(ds, 'SeriesTime', ''),
        "series_instance_uid": safe_get_tag(ds, 'SeriesInstanceUID', ''),
        
        # Equipment Information
        "modality": safe_get_tag(ds, 'Modality', 'Unknown'),
        "manufacturer": safe_get_tag(ds, 'Manufacturer', ''),
        "manufacturer_model": safe_get_tag(ds, 'ManufacturerModelName', ''),
        "software_versions": safe_get_tag(ds, 'SoftwareVersions', ''),
        
        # Image Properties
        "body_part_examined": safe_get_tag(ds, 'BodyPartExamined', ''),
        "slice_thickness": safe_get_tag(ds, 'SliceThickness', ''),
        "spacing_between_slices": safe_get_tag(ds, 'SpacingBetweenSlices', ''),
        "pixel_spacing": safe_get_tag(ds, 'PixelSpacing', []),
        "rows": safe_get_tag(ds, 'Rows', 0),
        "columns": safe_get_tag(ds, 'Columns', 0),
        
        # MR Specific (if present)
        "mr_acquisition_type": safe_get_tag(ds, 'MRAcquisitionType', ''),
        "scanning_sequence": safe_get_tag(ds, 'ScanningSequence', ''),
        "sequence_name": safe_get_tag(ds, 'SequenceName', ''),
        "echo_time": safe_get_tag(ds, 'EchoTime', ''),
        "repetition_time": safe_get_tag(ds, 'RepetitionTime', ''),
        "magnetic_field_strength": safe_get_tag(ds, 'MagneticFieldStrength', ''),
        
        # Processing metadata
        "total_slices": total_slices
    }


def extract_slice_metadata(ds: pydicom.Dataset, index: int, filename: str) -> Dict[str, Any]:
    """
    Extract metadata specific to individual slice.
    Based on actual DICOM tags found in sample MRI file (0002.DCM).
    """
    return {
        # File/Index Information
        "index": index,
        "filename": filename,
        
        # Instance Information
        "instance_number": safe_get_tag(ds, 'InstanceNumber', index + 1),
        "sop_instance_uid": safe_get_tag(ds, 'SOPInstanceUID', ''),
        
        # Acquisition Information
        "acquisition_date": safe_get_tag(ds, 'AcquisitionDate', ''),
        "acquisition_time": safe_get_tag(ds, 'AcquisitionTime', ''),
        "content_date": safe_get_tag(ds, 'ContentDate', ''),
        "content_time": safe_get_tag(ds, 'ContentTime', ''),
        
        # Spatial Information
        "slice_location": safe_get_tag(ds, 'SliceLocation', ''),
        "image_position_patient": safe_get_tag(ds, 'ImagePositionPatient', []),
        "image_orientation_patient": safe_get_tag(ds, 'ImageOrientationPatient', []),
        
        # Image Properties
        "rows": int(ds.Rows) if hasattr(ds, 'Rows') else 0,
        "columns": int(ds.Columns) if hasattr(ds, 'Columns') else 0,
        "pixel_spacing": safe_get_tag(ds, 'PixelSpacing', []),
        
        # Display Properties
        "window_center": safe_get_tag(ds, 'WindowCenter', ''),
        "window_width": safe_get_tag(ds, 'WindowWidth', ''),
        "window_explanation": safe_get_tag(ds, 'WindowCenterWidthExplanation', ''),
        
        # Image Type and Quality
        "image_type": safe_get_tag(ds, 'ImageType', []),
        "photometric_interpretation": safe_get_tag(ds, 'PhotometricInterpretation', ''),
        "smallest_pixel_value": safe_get_tag(ds, 'SmallestImagePixelValue', ''),
        "largest_pixel_value": safe_get_tag(ds, 'LargestImagePixelValue', ''),
    }


def safe_get_tag(ds: pydicom.Dataset, tag_name: str, default: Any) -> Any:
    """
    Safely retrieve DICOM tag value with fallback to default.
    Handles type conversions for JSON serialization.
    """
    try:
        if not hasattr(ds, tag_name):
            return default
        
        value = getattr(ds, tag_name)
        
        # Handle bytes
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore').strip()
        
        # Handle PersonName
        if hasattr(value, 'decode'):
            return str(value).strip()
        
        # Handle MultiValue (arrays)
        if hasattr(value, '__iter__') and not isinstance(value, str):
            return [float(v) if isinstance(v, (int, float)) else str(v) for v in value]
        
        # Return as-is for primitives
        return value if value != '' else default
        
    except Exception as e:
        print(f"Error extracting tag {tag_name}: {e}")
        return default


def cleanup_all_temp_folders():
    """
    Called on server shutdown to clean up all temp folders.
    """
    import shutil
    for folder in active_temp_folders:
        try:
            if Path(folder).exists():
                shutil.rmtree(folder)
                print(f"Cleaned up: {folder}")
        except Exception as e:
            print(f"Error cleaning up {folder}: {e}")

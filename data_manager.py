"""
Data management module for Tainan 2024 Drone Multispectral & Vegetation Index data.
Handles CSV loading, column categorization, metadata extraction, spatial matrix generation,
and statistical computations for visualization.
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

class DataManager:
    def __init__(self, csv_path: Optional[str] = "Tainan2024.csv"):
        self.csv_path = csv_path
        self.df: pd.DataFrame = pd.DataFrame()
        self.metadata_cols: List[str] = []
        self.metric_cols: List[str] = []
        self.image_cols: List[str] = []
        self.trait_catalog: List[Dict[str, Any]] = []
        self.image_catalog: List[Dict[str, Any]] = []
        self.col_to_alias: Dict[str, str] = {}
        self.alias_to_col: Dict[str, str] = {}
        self.study_info: Dict[str, Any] = {
            "studyYear": "-", "programName": "-", "studyName": "Please Upload CSV",
            "studyDescription": "", "studyDesign": "", "locationName": "",
            "totalPlots": 0, "totalGermplasms": 0, "replicates": [],
            "maxRow": 0, "minRow": 0, "maxCol": 0, "minCol": 0,
            "totalMetrics": 0, "totalImages": 0
        }
        if csv_path and os.path.exists(csv_path):
            self.load_data(csv_path)

    def load_data(self, csv_path: str):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset not found at {csv_path}")

        self.csv_path = csv_path
        df = pd.read_csv(csv_path)

        # Convert rowNumber, colNumber, plotNumber, replicate to int where possible
        for col in ["rowNumber", "colNumber", "plotNumber", "replicate"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        self.df = df
        self._analyze_columns()
        self._extract_study_info()

    def _analyze_columns(self):
        df = self.df
        self.metadata_cols = [
            "studyYear", "programDbId", "programName", "programDescription",
            "studyDbId", "studyName", "studyDescription", "studyDesign",
            "plotWidth", "plotLength", "fieldSize", "plantingDate", "harvestDate",
            "locationDbId", "locationName", "germplasmDbId", "germplasmName",
            "observationLevel", "observationUnitDbId", "observationUnitName",
            "replicate", "blockNumber", "plotNumber", "rowNumber", "colNumber",
            "entryType", "plantNumber"
        ]
        self.metadata_cols = [c for c in self.metadata_cols if c in df.columns]

        # Identify image columns (contain http/https or image filenames)
        self.image_cols = []
        for c in df.columns:
            first_val = str(df[c].dropna().iloc[0]) if not df[c].dropna().empty else ""
            if "http://" in first_val or "https://" in first_val or ".png" in first_val or ".jpg" in first_val:
                self.image_cols.append(c)

        # Catalog images with human-readable labels and categories
        self.image_catalog = []
        for col in self.image_cols:
            cat = "Spectral Bands"
            label = col
            key = "other"
            
            # Extract readable label from long column name
            if "polygon_rgb_imagery" in col:
                label = "RGB Natural Color Imagery"
                cat = "RGB"
                key = "rgb"
            elif "polygon_ndvi_imagery" in col:
                label = "NDVI Vegetation Index Imagery"
                cat = "Vegetation Indices"
                key = "ndvi"
            elif "polygon_ndre_imagery" in col:
                label = "NDRE Vegetation Index Imagery"
                cat = "Vegetation Indices"
                key = "ndre"
            elif "polygon_ccc_imagery" in col:
                label = "CCC Canopy Chlorophyll Content Imagery"
                cat = "Vegetation Indices"
                key = "ccc"
            elif "polygon_tgi_imagery" in col:
                label = "TGI Triangular Greenness Index Imagery"
                cat = "Vegetation Indices"
                key = "tgi"
            elif "polygon_vari_imagery" in col:
                label = "VARI Visible Atmospherically Resistant Imagery"
                cat = "Vegetation Indices"
                key = "vari"
            elif "polygon_nrn_imagery" in col:
                label = "NRN False Color Imagery (NIR-Red-NIR)"
                cat = "False Color Indices"
                key = "nrn"
            elif "polygon_nren_imagery" in col:
                label = "NReN False Color Imagery (NIR-RedEdge-NIR)"
                cat = "False Color Indices"
                key = "nren"
            elif "blue_background_removed" in col:
                label = "Blue Band (Thresholded / BG Removed)"
                cat = "Thresholded Bands"
                key = "blue_thresholded"
            elif "polygon_blue_imagery" in col:
                label = "Blue Band Reflectance (450-520nm)"
                cat = "Reflectance Bands"
                key = "blue"
            elif "green_background_removed" in col:
                label = "Green Band (Thresholded / BG Removed)"
                cat = "Thresholded Bands"
                key = "green_thresholded"
            elif "polygon_green_imagery" in col:
                label = "Green Band Reflectance (515-600nm)"
                cat = "Reflectance Bands"
                key = "green"
            elif "red_background_removed" in col:
                label = "Red Band (Thresholded / BG Removed)"
                cat = "Thresholded Bands"
                key = "red_thresholded"
            elif "polygon_red_imagery" in col:
                label = "Red Band Reflectance (600-690nm)"
                cat = "Reflectance Bands"
                key = "red"
            elif "red_edge_background_removed" in col:
                label = "Red Edge Band (Thresholded / BG Removed)"
                cat = "Thresholded Bands"
                key = "red_edge_thresholded"
            elif "polygon_red_edge_imagery" in col:
                label = "Red Edge Band Reflectance (690-750nm)"
                cat = "Reflectance Bands"
                key = "red_edge"
            elif "nir_background_removed" in col:
                label = "NIR Band (Thresholded / BG Removed)"
                cat = "Thresholded Bands"
                key = "nir_thresholded"
            elif "polygon_nir_imagery" in col:
                label = "NIR Band Reflectance (780-3000nm)"
                cat = "Reflectance Bands"
                key = "nir"

            self.image_catalog.append({
                "column": col,
                "label": label,
                "category": cat,
                "key": key
            })

        # Identify numeric metric columns (those containing '|')
        self.metric_cols = [c for c in df.columns if "|" in c]
        self.trait_catalog = []
        self.col_to_alias = {}
        self.alias_to_col = {}

        for col in self.metric_cols:
            parts = col.split("|")
            stat = parts[0].strip()
            band = parts[1].strip() if len(parts) > 1 else ""
            subtype = parts[2].strip() if len(parts) > 2 else ""

            # Classify category
            if "NDVI" in subtype:
                cat = "Vegetation Indices"
                short_name = f"{stat} - NDVI"
            elif "NDRE" in subtype:
                cat = "Vegetation Indices"
                short_name = f"{stat} - NDRE"
            elif "CCC" in subtype:
                cat = "Vegetation Indices"
                short_name = f"{stat} - CCC"
            elif "TGI" in subtype:
                cat = "Vegetation Indices"
                short_name = f"{stat} - TGI"
            elif "VARI" in subtype:
                cat = "Vegetation Indices"
                short_name = f"{stat} - VARI"
            elif "Thresholded" in subtype:
                cat = "Thresholded Bands"
                short_name = f"{stat} - {subtype.replace('Thresholded ', '').replace(' Denoised Original Image', '')} (Thresholded)"
            else:
                cat = "Reflectance Bands"
                short_name = f"{stat} - {subtype.replace(' Denoised Original Image', '')}"

            # Create clean alias
            alias = re.sub(r'[^a-zA-Z0-9_]', '_', short_name).lower()
            alias = re.sub(r'_+', '_', alias).strip('_')
            
            # Avoid collision
            base_alias = alias
            counter = 1
            while alias in self.alias_to_col:
                alias = f"{base_alias}_{counter}"
                counter += 1

            self.col_to_alias[col] = alias
            self.alias_to_col[alias] = col

            self.trait_catalog.append({
                "column": col,
                "alias": alias,
                "name": short_name,
                "statistic": stat,
                "target": band,
                "subtype": subtype,
                "category": cat,
                "is_primary": ("Mean Pixel Value" in stat and ("NDVI" in subtype or "NDRE" in subtype or "CCC" in subtype or "TGI" in subtype or "VARI" in subtype or "NIR" in subtype or "Red" in subtype))
            })

    def _extract_study_info(self):
        df = self.df
        self.study_info = {
            "studyYear": str(df["studyYear"].iloc[0]) if "studyYear" in df.columns else "2024",
            "programName": str(df["programName"].iloc[0]) if "programName" in df.columns else "NTU",
            "studyName": str(df["studyName"].iloc[0]) if "studyName" in df.columns else "TNDAIS Sheath Blight",
            "studyDescription": str(df["studyDescription"].iloc[0]) if "studyDescription" in df.columns else "2nd season sheath blight",
            "studyDesign": str(df["studyDesign"].iloc[0]) if "studyDesign" in df.columns else "greenhouse",
            "locationName": str(df["locationName"].iloc[0]) if "locationName" in df.columns else "Tainan DARES",
            "totalPlots": int(len(df)),
            "totalGermplasms": int(df["germplasmName"].nunique()) if "germplasmName" in df.columns else 0,
            "replicates": [int(r) for r in sorted(df["replicate"].unique().tolist())] if "replicate" in df.columns else [],
            "maxRow": int(df["rowNumber"].max()) if "rowNumber" in df.columns else 90,
            "minRow": int(df["rowNumber"].min()) if "rowNumber" in df.columns else 1,
            "maxCol": int(df["colNumber"].max()) if "colNumber" in df.columns else 4,
            "minCol": int(df["colNumber"].min()) if "colNumber" in df.columns else 1,
            "totalMetrics": len(self.metric_cols),
            "totalImages": len(self.image_cols)
        }

    def resolve_column(self, col_or_alias: str) -> str:
        """Resolves either a direct column name or an alias to the actual DataFrame column."""
        if col_or_alias in self.df.columns:
            return col_or_alias
        if col_or_alias in self.alias_to_col:
            return self.alias_to_col[col_or_alias]
        # Fuzzy match by short label or metric name
        for item in self.trait_catalog:
            if col_or_alias.lower() == item["name"].lower() or col_or_alias.lower() == item["alias"].lower():
                return item["column"]
        # Default fallback to Mean NDVI
        default_col = self.get_default_metric()
        return default_col

    def get_default_metric(self) -> str:
        for item in self.trait_catalog:
            if item["statistic"] == "Mean Pixel Value" and "NDVI" in item["subtype"]:
                return item["column"]
        return self.metric_cols[0] if self.metric_cols else ""

    def get_metadata_summary(self) -> Dict[str, Any]:
        return {
            "info": self.study_info,
            "primaryTraits": [
                {
                    "alias": item["alias"],
                    "name": item["name"],
                    "column": item["column"],
                    "category": item["category"]
                }
                for item in self.trait_catalog if item.get("is_primary")
            ],
            "categories": sorted(list(set(item["category"] for item in self.trait_catalog))),
            "imageCategories": sorted(list(set(item["category"] for item in self.image_catalog)))
        }

    def get_traits(self, category: Optional[str] = None, stat: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.trait_catalog
        if category:
            results = [r for r in results if r["category"].lower() == category.lower()]
        if stat:
            results = [r for r in results if r["statistic"].lower() == stat.lower()]
        return results

    def get_image_list(self) -> List[Dict[str, Any]]:
        return self.image_catalog

    def get_field_heatmap_data(self, metric_col: str, replicate: Optional[int] = None) -> Dict[str, Any]:
        col = self.resolve_column(metric_col)
        df = self.df.copy()

        if replicate and replicate in [1, 2]:
            df = df[df["replicate"] == replicate]

        # Ensure numeric
        df["val"] = pd.to_numeric(df[col], errors="coerce")
        valid_df = df.dropna(subset=["val"])

        min_val = float(valid_df["val"].min()) if not valid_df.empty else 0.0
        max_val = float(valid_df["val"].max()) if not valid_df.empty else 1.0
        mean_val = float(valid_df["val"].mean()) if not valid_df.empty else 0.0

        # Construct spatial cells list
        cells = []
        for _, row in df.iterrows():
            val = float(row["val"]) if pd.notnull(row["val"]) else None
            cells.append({
                "row": int(row["rowNumber"]),
                "col": int(row["colNumber"]),
                "plotNumber": int(row["plotNumber"]),
                "replicate": int(row["replicate"]),
                "germplasmName": str(row["germplasmName"]),
                "observationUnitName": str(row["observationUnitName"]),
                "value": round(val, 5) if val is not None else None
            })

        # Also prepare 2D matrix (rows: 1..90, cols: 1..4)
        min_r = int(self.study_info["minRow"])
        max_r = int(self.study_info["maxRow"])
        min_c = int(self.study_info["minCol"])
        max_c = int(self.study_info["maxCol"])

        cols_range = list(range(min_c, max_c + 1)) if not replicate else ([3, 4] if replicate == 1 else [1, 2])
        rows_range = list(range(min_r, max_r + 1))

        # Build grid z matrix [rows][cols]
        lookup = {(c["row"], c["col"]): c for c in cells}
        z_matrix = []
        text_matrix = []
        hover_matrix = []

        for r in rows_range:
            row_vals = []
            row_text = []
            row_hover = []
            for c in cols_range:
                cell = lookup.get((r, c))
                if cell and cell["value"] is not None:
                    row_vals.append(cell["value"])
                    row_text.append(f"{cell['plotNumber']}")
                    row_hover.append(
                        f"Plot: {cell['plotNumber']}<br>"
                        f"Germplasm: {cell['germplasmName']}<br>"
                        f"Rep: {cell['replicate']} | Row: {r}, Col: {c}<br>"
                        f"Value: {cell['value']}"
                    )
                else:
                    row_vals.append(None)
                    row_text.append("")
                    row_hover.append(f"Row {r}, Col {c}: Empty")
            z_matrix.append(row_vals)
            text_matrix.append(row_text)
            hover_matrix.append(row_hover)

        trait_meta = next((item for item in self.trait_catalog if item["column"] == col), {
            "name": col, "category": "Metric"
        })

        return {
            "metricColumn": col,
            "metricName": trait_meta.get("name", col),
            "category": trait_meta.get("category", "Metric"),
            "statistic": trait_meta.get("statistic", ""),
            "min": min_val,
            "max": max_val,
            "mean": mean_val,
            "replicate": replicate,
            "rows": rows_range,
            "cols": cols_range,
            "z": z_matrix,
            "text": text_matrix,
            "hover": hover_matrix,
            "cells": cells
        }

    def get_distribution_data(self, metric_col: str, replicate: Optional[int] = None, num_bins: int = 25) -> Dict[str, Any]:
        col = self.resolve_column(metric_col)
        df = self.df.copy()
        df["val"] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["val"])

        trait_meta = next((item for item in self.trait_catalog if item["column"] == col), {"name": col})

        def _calc_stats(series: pd.Series) -> Dict[str, Any]:
            if series.empty:
                return {}
            v = series.values
            return {
                "count": int(len(v)),
                "mean": round(float(np.mean(v)), 5),
                "std": round(float(np.std(v, ddof=1)), 5) if len(v) > 1 else 0.0,
                "median": round(float(np.median(v)), 5),
                "min": round(float(np.min(v)), 5),
                "max": round(float(np.max(v)), 5),
                "q25": round(float(np.percentile(v, 25)), 5),
                "q75": round(float(np.percentile(v, 75)), 5),
                "iqr": round(float(np.percentile(v, 75) - np.percentile(v, 25)), 5),
                "skew": round(float(stats.skew(v)), 3) if len(v) > 2 else 0.0
            }

        overall_stats = _calc_stats(df["val"])

        # Create histogram bins
        counts, bin_edges = np.histogram(df["val"], bins=num_bins)
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

        # KDE approximation curve if enough points
        kde_x, kde_y = [], []
        if len(df["val"]) > 5:
            try:
                kde = stats.gaussian_kde(df["val"])
                kde_x = np.linspace(bin_edges[0], bin_edges[-1], 100).tolist()
                kde_y = kde(kde_x).tolist()
            except Exception:
                pass

        # Split by replicate
        rep1_vals = df[df["replicate"] == 1]["val"].tolist()
        rep2_vals = df[df["replicate"] == 2]["val"].tolist()

        return {
            "metricColumn": col,
            "metricName": trait_meta.get("name", col),
            "stats": overall_stats,
            "bins": [round(float(b), 5) for b in bin_edges],
            "binCenters": [round(float(b), 5) for b in bin_centers],
            "counts": [int(c) for c in counts],
            "kde": {"x": [round(float(x), 5) for x in kde_x], "y": [round(float(y), 5) for y in kde_y]},
            "allValues": [round(float(v), 5) for v in df["val"]],
            "rep1Values": [round(float(v), 5) for v in rep1_vals],
            "rep2Values": [round(float(v), 5) for v in rep2_vals],
            "rep1Stats": _calc_stats(pd.Series(rep1_vals)),
            "rep2Stats": _calc_stats(pd.Series(rep2_vals)),
            "plots": [
                {
                    "plotNumber": int(r["plotNumber"]),
                    "germplasmName": str(r["germplasmName"]),
                    "replicate": int(r["replicate"]),
                    "value": round(float(r["val"]), 5)
                }
                for _, r in df.iterrows()
            ]
        }

    def get_scatter_data(self, x_metric: str, y_metric: str, color_by: str = "replicate", replicate: Optional[int] = None) -> Dict[str, Any]:
        x_col = self.resolve_column(x_metric)
        y_col = self.resolve_column(y_metric)
        df = self.df.copy()

        if replicate and replicate in [1, 2]:
            df = df[df["replicate"] == replicate]

        df["x_val"] = pd.to_numeric(df[x_col], errors="coerce")
        df["y_val"] = pd.to_numeric(df[y_col], errors="coerce")
        df = df.dropna(subset=["x_val", "y_val"])

        trait_x = next((item for item in self.trait_catalog if item["column"] == x_col), {"name": x_col})
        trait_y = next((item for item in self.trait_catalog if item["column"] == y_col), {"name": y_col})

        # Calculate regression and correlation
        x_arr = df["x_val"].values
        y_arr = df["y_val"].values
        
        reg_stats = {}
        trendline = []
        if len(x_arr) > 2:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_arr, y_arr)
            r2 = r_value ** 2
            reg_stats = {
                "slope": round(float(slope), 5),
                "intercept": round(float(intercept), 5),
                "r": round(float(r_value), 4),
                "r2": round(float(r2), 4),
                "pValue": float(p_value),
                "stdErr": round(float(std_err), 5),
                "equation": f"y = {slope:.4f}x + {intercept:.4f} (R² = {r2:.4f}, r = {r_value:.4f})"
            }
            # Min and max x for trendline
            x_min = float(np.min(x_arr))
            x_max = float(np.max(x_arr))
            trendline = [
                {"x": x_min, "y": float(slope * x_min + intercept)},
                {"x": x_max, "y": float(slope * x_max + intercept)}
            ]

        # Build points
        points = []
        for _, row in df.iterrows():
            c_val = str(row[color_by]) if color_by in df.columns else str(row["replicate"])
            points.append({
                "plotNumber": int(row["plotNumber"]),
                "germplasmName": str(row["germplasmName"]),
                "replicate": int(row["replicate"]),
                "row": int(row["rowNumber"]),
                "col": int(row["colNumber"]),
                "x": round(float(row["x_val"]), 5),
                "y": round(float(row["y_val"]), 5),
                "color": c_val
            })

        return {
            "xColumn": x_col,
            "yColumn": y_col,
            "xName": trait_x.get("name", x_col),
            "yName": trait_y.get("name", y_col),
            "colorBy": color_by,
            "regression": reg_stats,
            "trendline": trendline,
            "points": points
        }

    def get_correlation_matrix(self, trait_aliases: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculates multi-trait correlation matrix for prominent vegetation indices and bands."""
        if not trait_aliases:
            # Default to primary Mean pixel values
            default_traits = [
                ("Mean Pixel Value", "NDVI Vegetative Index Image"),
                ("Mean Pixel Value", "NDRE Vegetative Index Image"),
                ("Mean Pixel Value", "CCC Vegetative Index Image"),
                ("Mean Pixel Value", "TGI Vegetative Index Image"),
                ("Mean Pixel Value", "VARI Vegetative Index Image"),
                ("Mean Pixel Value", "Blue Denoised Original Image"),
                ("Mean Pixel Value", "Green Denoised Original Image"),
                ("Mean Pixel Value", "Red Denoised Original Image"),
                ("Mean Pixel Value", "Red Edge Denoised Original Image"),
                ("Mean Pixel Value", "NIR Denoised Original Image")
            ]
            cols = []
            for stat_name, sub_name in default_traits:
                match = [c for c in self.metric_cols if c.startswith(stat_name) and sub_name in c]
                if match:
                    cols.append(match[0])
        else:
            cols = [self.resolve_column(a) for a in trait_aliases]

        labels = []
        for col in cols:
            item = next((t for t in self.trait_catalog if t["column"] == col), None)
            if item:
                # Shorten label for clean matrix display
                name = item["name"].replace("Mean Pixel Value - ", "").replace("Median Pixel Value - ", "")
                labels.append(name)
            else:
                labels.append(col)

        sub_df = self.df[cols].apply(pd.to_numeric, errors="coerce")
        corr_matrix = sub_df.corr(method="pearson").round(3)

        z = corr_matrix.values.tolist()

        return {
            "columns": cols,
            "labels": labels,
            "z": z
        }

    def get_plot_details(self, plot_identifier: Any) -> Optional[Dict[str, Any]]:
        df = self.df
        row = None
        
        # Match by plotNumber
        try:
            p_num = int(plot_identifier)
            match = df[df["plotNumber"] == p_num]
            if not match.empty:
                row = match.iloc[0]
        except (ValueError, TypeError):
            pass

        # Match by observationUnitName
        if row is None and isinstance(plot_identifier, str):
            match = df[df["observationUnitName"] == plot_identifier]
            if not match.empty:
                row = match.iloc[0]

        if row is None:
            return None

        # Build plot metadata
        plot_meta = {
            "plotNumber": int(row["plotNumber"]),
            "observationUnitName": str(row["observationUnitName"]),
            "germplasmName": str(row["germplasmName"]),
            "replicate": int(row["replicate"]),
            "rowNumber": int(row["rowNumber"]),
            "colNumber": int(row["colNumber"]),
            "blockNumber": int(row["blockNumber"]) if "blockNumber" in row else 1,
            "entryType": str(row["entryType"]) if "entryType" in row else "test",
            "studyName": str(row.get("studyName", self.study_info.get("studyName", ""))),
            "plantingDate": str(row.get("plantingDate", "")),
            "harvestDate": str(row.get("harvestDate", ""))
        }

        # Key vegetation index values
        vi_values = {}
        for item in self.trait_catalog:
            if item["statistic"] == "Mean Pixel Value":
                col = item["column"]
                val = row.get(col)
                if pd.notnull(val):
                    clean_name = item["name"].replace("Mean Pixel Value - ", "")
                    vi_values[clean_name] = round(float(val), 5)

        # Spectral reflectance profile
        # Blue: ~485nm, Green: ~560nm, Red: ~645nm, Red Edge: ~720nm, NIR: ~840nm
        bands_data = []
        band_wavelengths = [
            ("Blue", 485, "Blue (450-520nm)"),
            ("Green", 560, "Green (515-600nm)"),
            ("Red", 645, "Red (600-690nm)"),
            ("Red Edge", 720, "Red Edge (690-750nm)"),
            ("NIR", 840, "NIR (780-3000nm)")
        ]
        
        for b_name, wl, target in band_wavelengths:
            # find original arithmetic mean col
            orig_col = next((c for c in self.metric_cols if c.startswith("Mean Pixel Value") and target in c and "Thresholded" not in c), None)
            val = float(row[orig_col]) if orig_col and pd.notnull(row[orig_col]) else None
            
            # calculate field mean for this band
            field_avg = float(df[orig_col].mean()) if orig_col and orig_col in df.columns else None

            bands_data.append({
                "band": b_name,
                "wavelength": wl,
                "value": round(val, 5) if val is not None else None,
                "fieldAverage": round(field_avg, 5) if field_avg is not None else None
            })

        # Images dictionary
        images = []
        for img_info in self.image_catalog:
            col = img_info["column"]
            url = str(row.get(col, ""))
            if url and ("http://" in url or "https://" in url or ".png" in url):
                images.append({
                    "key": img_info["key"],
                    "label": img_info["label"],
                    "category": img_info["category"],
                    "url": url
                })

        return {
            "metadata": plot_meta,
            "indices": vi_values,
            "spectralSignature": bands_data,
            "images": images
        }

    def get_germplasm_ranking(self, metric_col: str, top_n: int = 15, ascending: bool = False) -> Dict[str, Any]:
        col = self.resolve_column(metric_col)
        df = self.df.copy()
        df["val"] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["val"])

        trait_meta = next((item for item in self.trait_catalog if item["column"] == col), {"name": col})

        # Group by germplasm
        grouped = df.groupby("germplasmName")["val"].agg(["mean", "std", "count", "min", "max"]).reset_index()
        grouped = grouped.sort_values(by="mean", ascending=ascending)
        top_subset = grouped.head(top_n)

        germplasms = top_subset["germplasmName"].tolist()
        box_data = []
        for g in germplasms:
            g_df = df[df["germplasmName"] == g]
            rep1_v = g_df[g_df["replicate"] == 1]["val"].tolist()
            rep2_v = g_df[g_df["replicate"] == 2]["val"].tolist()
            box_data.append({
                "germplasm": g,
                "mean": round(float(g_df["val"].mean()), 5),
                "values": [round(float(x), 5) for x in g_df["val"]],
                "rep1": [round(float(x), 5) for x in rep1_v],
                "rep2": [round(float(x), 5) for x in rep2_v]
            })

        return {
            "metricColumn": col,
            "metricName": trait_meta.get("name", col),
            "ascending": ascending,
            "rankings": box_data
        }

    def search_plots(self, query: str = "", replicate: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df.copy()
        if replicate and replicate in [1, 2]:
            df = df[df["replicate"] == replicate]

        if query:
            q = str(query).lower()
            df = df[
                df["plotNumber"].astype(str).str.contains(q) |
                df["germplasmName"].astype(str).str.lower().contains(q) |
                df["observationUnitName"].astype(str).str.lower().contains(q)
            ]

        results = []
        for _, r in df.head(50).iterrows():
            results.append({
                "plotNumber": int(r["plotNumber"]),
                "germplasmName": str(r["germplasmName"]),
                "replicate": int(r["replicate"]),
                "rowNumber": int(r["rowNumber"]),
                "colNumber": int(r["colNumber"]),
                "observationUnitName": str(r["observationUnitName"])
            })
        return results

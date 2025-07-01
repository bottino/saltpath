import argparse
import math
import os
import shutil

import geopandas as gpd
import gpxpy
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point


def main(input_file, output_dir, tolerance, dir_name):
    if dir_name is None:
        name_gdf = gpd.read_file(input_file, layer="tracks")
        dir_name = name_gdf.iloc[0]["name"]

    if os.path.exists(dir_name) and os.path.isdir(dir_name):
        shutil.rmtree(dir_name)

    os.makedirs(dir_name)
    output_path = os.path.join(output_dir, dir_name)

    # Read file
    gdf = gpd.read_file(input_file, layer="track_points")
    gdf = gdf.dropna(axis=1, how="all")

    # convert to https://epsg.io/21781
    proj_gdf = gdf.to_crs(21781)

    # simplify the track
    path_gdf = simplify_path(proj_gdf, tolerance)

    # join with the timestamps and indices
    path_gdf = gpd.sjoin(path_gdf, proj_gdf, how="left")

    # export the simplified path to inspect as gpx
    export_to_gpx(path_gdf, os.path.join(output_path, "simplified_path.gpx"))
    # copy the raw data file
    shutil.copy(input_file, output_path)

    # output tacks
    tacks_df = get_tacks(path_gdf)
    tacks_df.to_csv(os.path.join(output_path, "tacks.csv"), index=None)


# Use RDP algorithm: https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm
def simplify_path(gdf: gpd.GeoDataFrame, tolerance: float) -> gpd.GeoDataFrame:
    path = LineString(gdf.geometry.tolist())
    simple_line = path.simplify(tolerance, preserve_topology=False)
    simple_points = [Point(c) for c in simple_line.coords]
    return gpd.GeoDataFrame(geometry=simple_points, crs=gdf.crs)


def calculate_course(dx, dy):
    angle_rad = math.atan2(
        dx, dy
    )  # dx first because the convention is angle clockwise, starting from y-axis
    angle_deg = math.degrees(angle_rad)
    return (angle_deg + 360) % 360  # [0, 360[


def get_tacks(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    gdf["x"] = gdf.geometry.x
    gdf["y"] = gdf.geometry.y
    gdf["x_next"] = gdf["x"].shift(-1)
    gdf["y_next"] = gdf["y"].shift(-1)
    gdf["time_next"] = gdf["time"].shift(-1)
    gdf = gdf[:-1].copy()  # remove last row

    df = pd.DataFrame(
        {
            "start_point": list(zip(round(gdf.x, 2), round(gdf.y, 2))),
            "end_point": list(zip(round(gdf.x_next, 2), round(gdf.y_next, 2))),
            "start_time": gdf.time,
            "end_time": gdf.time_next,
            "distance_m": round(
                np.sqrt(
                    (gdf["x_next"] - gdf["x"]) ** 2 + (gdf["y_next"] - gdf["y"]) ** 2
                ),
                2,
            ),
            "course_deg": round(
                gdf.apply(
                    lambda row: calculate_course(
                        row["x_next"] - row["x"], row["y_next"] - row["y"]
                    ),
                    axis=1,
                ),
                2,
            ),
        }
    )

    df["duration_s"] = (df["end_time"] - df["start_time"]).dt.seconds
    df["speed_ms"] = df.apply(lambda row: row["distance_m"] / row["duration_s"], axis=1)
    df["speed_kts"] = round(df["speed_ms"] * 1.94384, 2)

    return df


def export_to_gpx(gdf: gpd.GeoDataFrame, output_file: str) -> None:
    # convert to lat long
    gdf = gdf.to_crs(4326)

    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for idx, row in gdf.iterrows():
        point = row.geometry
        gpx_point = gpxpy.gpx.GPXTrackPoint(
            latitude=point.y,
            longitude=point.x,
            elevation=row.get("ele"),
            time=row.get("time"),
        )
        gpx_segment.points.append(gpx_point)

    with open(output_file, "w") as f:
        f.write(gpx.to_xml())


# Step 3: Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Simplify a track on a GPX file, and outputs the simplified path and the tacks to an output directory."
    )
    parser.add_argument("input_file", type=str, help="Path to the input GPX file")
    parser.add_argument(
        "output_dir",
        type=str,
        help="Directory where the output is stored",
    )
    parser.add_argument(
        "-t",
        "--tolerance",
        type=float,
        default=200.0,
        help="Tolerance value for simplification in meters. Higher values will result in a trajectory with fewer points.",
    )
    parser.add_argument(
        "-d",
        "--dir_name",
        type=str,
        default=None,
        help="Name of the output directory for the acquisition",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    main(args.input_file, args.output_dir, args.tolerance, args.dir_name)

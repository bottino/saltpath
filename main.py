import gpxpy

import geopandas as gpd


# Use RDP algorithm: https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm
def main():
    with open("./raw_path.gpx", "r") as f:
        gpx = gpxpy.parse(f)

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                print(f"Point: ({point.latitude, point.longitude})")


def gpdmain():
    gdf = gpd.read_file("./raw_path.gpx", layer="track_points")

    print(gdf.head())
    print(gdf.columns)
    gdf.plot()


if __name__ == "__main__":
    gpdmain()

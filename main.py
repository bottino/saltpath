import gpxpy


# Use RDP algorithm: https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm
def main():
    with open("./raw_path.gpx", "r") as f:
        gpx = gpxpy.parse(f)

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                print(f"Point: ({point.latitude, point.longitude})")


if __name__ == "__main__":
    main()

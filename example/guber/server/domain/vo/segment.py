import math

from example.guber.server.domain import Coord


class Segment:

    def __init__(self, from_coord: Coord, to_coord: Coord):
        if not from_coord or not to_coord:
            raise ValueError("Invalid segment")
        self.from_coord = from_coord
        self.to_coord = to_coord

    @property
    def distance(self) -> int:
        """Calculate distance between coordinates using Haversine formula."""
        earth_radius = 6371
        degrees_to_radians = math.pi / 180

        from_lat, from_lon = self.from_coord.lat, self.from_coord.long
        to_lat, to_lon = self.to_coord.lat, self.to_coord.long

        delta_lat = (to_lat - from_lat) * degrees_to_radians
        delta_lon = (to_lon - from_lon) * degrees_to_radians

        a = math.sin(delta_lat / 2) * math.sin(delta_lat / 2) + math.cos(
            from_lat * degrees_to_radians
        ) * math.cos(to_lat * degrees_to_radians) * math.sin(delta_lon / 2) * math.sin(
            delta_lon / 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = earth_radius * c
        return round(distance)

import numpy as np
from datetime import timedelta

try:
    from .exceptions import RallyStyleException, RallyResultsException, MatchCheckpointsException, CalcResultsException
except:
    from exceptions import RallyStyleException, RallyResultsException, MatchCheckpointsException, CalcResultsException


class RallyResults(object):
    """
    segments is the rally definition
    type_name: STRING "timed", "Transport"
    type_args: DICT, time_limit in sec for transport
    total_timed_types: DICT [gravel, uphill, road, ...]
    Segment structure:
  [{
    'segment_name':'Event Start',
    'location': {'lat': 39.737912, 'lon': -105.523881},
    'type_name': 'transport',
    'type_args': {'time_limit': 1800}
    total_timed_types: {'uphill':None(0), 'gravel': None}
  },]

  result structure:
  [{
    'segment_name': 'Event Start',
    'location': {'lat': 39.737912, 'lon': -105.523881},
    'type_name': 'transport',
    'type_args': {'time_limit': 1800}
    'duration': Timedelta('0 days 00:24:21'),
    'datetime': Timestamp('2012-07-21 09:18:13'),
    'total_timed': datetime.timedelta(0),
    total_timed_types: {'uphill':Timedelta(123), 'gravel': Timedelta(321)}
  },]
    """

    def __init__(self, df, segments):
        if {'Latitude', 'Longitude', 'Date_Time'}.intersection(set(df.columns)) != {'Latitude', 'Longitude',
                                                                                    'Date_Time'}:
            raise RallyStyleException(f"Dataframe must contains columns: \n {df.columns}")
        self.df = df
        self.init_columns = df.columns
        self.segments = segments
        self.epsilon = 0.00001  # used to for finding acute triangles
        self.near = .0002  # How near the point needs to be to the checkpoint.
        self.results = []
        # self.ck_points = pd.DataFrame([p['location'] for p in segments], columns=['Latitude', 'Longitude'])
        self.ck_points = [p['location'] for p in segments]
        if not 'shift_Longitude' in self.df.columns:
            self.df['shift_Longitude'] = self.df.shift(-1)['Longitude']
        if not 'shift_Latitude' in self.df.columns:
            self.df['shift_Latitude'] = self.df.shift(-1)['Latitude']
        # TODO It looks like we need to use this below instead os "to_next"
        if not 'dist_to_next' in self.df.columns:
            self.df['dist_to_next'] = np.linalg.norm(self.df[['Latitude', 'Longitude']].values -
                                                     self.df[['shift_Latitude', 'shift_Longitude']].values, axis=1)

    def check_bounds(self):
        latmax = min([ck['lat'] for ck in self.ck_points]) >= self.df.Latitude.min()
        lonmax = min([ck['lon'] for ck in self.ck_points]) >= self.df.Longitude.min()
        latmin = max([ck['lat'] for ck in self.ck_points]) <= self.df.Latitude.max()
        lonmin = max([ck['lon'] for ck in self.ck_points]) <= self.df.Longitude.max()
        assert latmax and lonmax and latmin and lonmin, "This activity does not seem to be within the area of the event segments"

    # TODO Use checkpoints module
    def match_checkpoints(self):
        """
        Identify the activity point the represents the arrival at the checkpoint
        find near points that form acute triangles
        """
        self.check_bounds()
        # the norm is the distance between two points.
        self.df['to_next'] = np.linalg.norm(self.df[['Latitude', 'Longitude']].values -
                                            self.df[['shift_Latitude', 'shift_Longitude']].values, axis=1)
        # self.df['checkpoint'] = np.nan
        row_slice = 0
        for i, ck in enumerate(self.ck_points):
            try:
                point = (ck['lat'], ck['lon'])
                # Calculate the distance from the chekpoint to all consecutive points in the data.
                self.df[f'ck_to_A{i}'] = np.linalg.norm(self.df[['Latitude', 'Longitude']].values - point, axis=1)
                self.df[f'ck_to_B{i}'] = np.linalg.norm(self.df[['shift_Latitude', 'shift_Longitude']].values - point,
                                                        axis=1)
                if self.df[f'ck_to_A{i}'].min() > self.near * 10:
                    raise MatchCheckpointsException(
                        f"It appears you never made it close to checkpoint {self.segments['segment_name']}")
                # Acute, For ck "i" if the angle between the lines ck:A and A:B acute. If so then ck is "between" A and B
                # Epislon is the fudge factor
                self.df['acute'] = self.df[f'ck_to_A{i}'] ** 2 + self.df['to_next'] ** 2 <= self.df[
                    f'ck_to_B{i}'] ** 2 + self.epsilon

                self.df.loc[
                    self.df[row_slice:][(self.df[row_slice:][f'ck_to_A{i}'] <= self.near) &
                                        (self.df[row_slice:].acute)].index[0], ['checkpoint']] = i
                row_slice = int(self.df[self.df.checkpoint == i].index[0])
                self.df['seg_duration'] = self.df[self.df.checkpoint >= 0]['Date_Time'].diff()
            except Exception as e:
                raise MatchCheckpointsException(
                    f"Fail on checkpoint:{i} location: {ck}\nDataframe columns:\n{self.df.columns}")

        self.df['seg_duration'] = self.df[self.df.checkpoint >= 0]['Date_Time'].diff()
        self.df['segment'] = self.df.checkpoint.fillna(method='ffill')
        self.df['segment'][self.df.segment >= len(self.ck_points) - 1] = np.nan

    def calc_results(self):
        """
        calculate and return results
        """
        total_timed = timedelta(seconds=0)
        for i, s in enumerate(self.segments[:-1]):
            r = s.copy()
            # print(i, s)
            duration = self.df.loc[self.df.checkpoint == i + 1]['seg_duration'].to_list()[0]
            date_time = self.df.loc[self.df.checkpoint == i]['Date_Time'].to_list()[0]
            r['duration'] = duration
            # self.segments[i]['date_time'] = date_time
            r['date_time'] = date_time
            if s['type_name'] == 'timed':
                total_timed = total_timed + duration
                r['total_timed'] = total_timed
            else:
                r['total_timed'] = total_timed
            self.results.append(r)

        date_time = self.df.loc[self.df.checkpoint == (len(self.segments) - 1)]['Date_Time'].to_list()[0]
        self.results.append(self.segments[-1])
        self.results[-1]['duration'] = None
        self.results[-1]['date_time'] = date_time
        self.results[-1]['total_timed'] = total_timed

        return self.results

    def export_lat_lon_alt(self, file_type='JSON'):
        """
        export the latitude and longitude
        :return: file
        """
        if file_type == 'JSON':
            return [dict(longitude=r.Longitude, latitude=r.Latitude, altitude=r.Altitude) for r in self.df.itertuples()]
        elif file_type == 'csv':
            self.df[['Latitude', 'Longitude']].to_csv('export.csv')

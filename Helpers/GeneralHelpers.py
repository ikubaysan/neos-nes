import cProfile
import pstats

class SpeedProfiler:
    def __init__(self):
        self.pr = cProfile.Profile()

    def start(self):
        self.pr.enable()

    def stop(self, num_results=20):
        self.pr.disable()
        stats = pstats.Stats(self.pr)
        #stats.sort_stats(pstats.SortKey.TIME)
        stats.sort_stats(pstats.SortKey.CUMULATIVE)
        stats.print_stats(num_results)

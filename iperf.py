class iperf_udp_client(object):
    def __init__(self, host, rate, duration, pkt_len):
        self.cmd = ['iperf', '-c', host, '-u', '-b', rate, '-t', duration, '-yC', '-xDC', '-l', pkt_len]

    def run(self):
        from subprocess import Popen, PIPE
        self.process = Popen(self.cmd, stdout=PIPE, stderr=PIPE)

    def result(self):
        self.process.wait()
        out,err = self.process.communicate()

        if err:
            print(err)

        return self.parse_result(out)

    @classmethod
    def parse_result(self, res):
        csv = res.strip().split(",")
        out = {}
        out['date'] = csv[0]
        out['remote_host'] = csv[1]
        out['remote_port'] = int(csv[2])
        out['local_host'] = csv[3]
        out['local_port'] = int(csv[4])
        out['connection'] = int(csv[5])
        out['duration'] = float(csv[6].split('-')[1])
        out['bytes'] = int(csv[7])
        out['rate'] = int(csv[8])
        out['jitter'] = float(csv[9])
        out['lost'] = int(csv[10])
        out['received'] = int(csv[11])
        out['loss_ratio'] = float(csv[12])
        out['delay'] = float(csv[13])

        return out

class iperf_udp_server(object):
    def __init__(self, pkt_len='1418'):
        self.cmd = ['iperf', '-s', '-u', '-l', pkt_len, '-yC']

    def run(self):
        from subprocess import Popen, PIPE
        self.process = Popen(self.cmd, stdout=PIPE, stderr=PIPE)

    def result(self):
        self.process.terminate()

        if not self.process.poll():
            self.process.kill()

        out,err = self.process.communicate()

        if err:
            print(err)

        return iperf_udp_client.parse_result(out)

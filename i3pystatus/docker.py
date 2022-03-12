import docker
from i3pystatus import IntervalModule


class Docker(IntervalModule):
    """
    Display information about docker containers
    Requires: docker
    """

    settings = (
        ("interval", "Update interval (in seconds)"),
        "format"
    )
    interval = 5
    format = "containers: {containers[running]} running/{containers[total]} total"

    def run(self):
        dclient = docker.from_env()

        docker_info = {
                'containers': {},
                'volumes': {},
                'images': {},
                'networks': {}}

        all_containers = dclient.containers.list(all=True)
        for container in all_containers:
            docker_info['containers'][container.status] = docker_info['containers'].get(container.status, 0) + 1
            docker_info['containers'][container.name] = container
            docker_info['containers'][container.name] = container.stats(stream=False)
            # Add some helper details
            docker_info['containers'][container.name]['memory_stats']['usage_kb'] = round(docker_info['containers'][container.name]['memory_stats'].get('usage', 0)/1024, 2)
            docker_info['containers'][container.name]['memory_stats']['usage_mb'] = round(docker_info['containers'][container.name]['memory_stats']['usage_kb']/1024, 2)
            docker_info['containers'][container.name]['memory_stats']['usage_gb'] = round(docker_info['containers'][container.name]['memory_stats']['usage_mb']/1024, 2)
        docker_info['containers']['total'] = len(all_containers)

        all_volumes = dclient.volumes.list()
        for volume in all_volumes:
            docker_info['volumes'][volume.name] = volume
        docker_info['volumes']['count'] = len(all_volumes)

        for image in dclient.images.list():
            docker_info['images']['id'] = image
        docker_info['images']['count'] = len(docker_info['images'])

        self.output = {
            "full_text": self.format.format(**docker_info),
            #"color": color
        }

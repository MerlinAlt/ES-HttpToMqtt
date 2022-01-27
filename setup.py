"""Setup file that defines the structure and dependencies of this module."""
from distutils.core import setup

REQUIREMENTS = ["fastapi",
                "pydantic",
                "paho-mqtt"]

setup(
    name='HttpToMqtt',
    version='0.0.1',
    packages=['HttpToMqtt', 'HttpToMqtt.Api', 'HttpToMqtt.Mqtt', 'HttpToMqtt.DataManager'],
    url='https://git.thm.de/softwaretechnik-projekt-pick-by-light-system-wise21_22/pbl-embedded-system/httptomqtt',
    install_requires=REQUIREMENTS,
    license='',
    author='Merlin Althoff',
    author_email='merlin.althoff@mni.thm.de',
    maintainer="Jens Fernández Mühlke",
    maintainer_email="jens.fernandez.muehlke@mni.thm.de",
    description='communication between ESP32 and backend'
)

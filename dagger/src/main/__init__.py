import dagger
import random
from dagger import dag, function, object_type


@object_type
class KillercodaCli:
    @function
    async def publish(self, source: dagger.Directory) -> str:
        """Publish the application container after building and testing it on-the-fly"""
        # call Dagger Function to run unit tests
        await self.test(source)
        # call Dagger Function to build the application image
        # publish the image to ttl.sh
        return await self.build(source).publish(
            f"ttl.sh/killercoda-cli-{random.randrange(10 ** 8)}"
        )

    @function
    def build(self, source: dagger.Directory) -> dagger.Container:
        """Build the application container"""
        build = (
            self.build_env(source)
            .with_exec(["hatch", "build"])
        )
        return (
            dag.container()
            .from_("python:3.10-slim")
            .with_directory("/dist", build.directory("/src/dist"))
        )

    @function
    async def test(self, source: dagger.Directory) -> str:
        """Run unit tests and generate coverage report"""
        return (
                await (
                    self.build_env(source)
                        .with_exec(["hatch", "run", "test:unit"])
                        .stdout()
                        )
                )

    @function
    def build_env(self, source: dagger.Directory) -> dagger.Container:
        """Build a ready-to-use development environment"""
        python_cache = dag.cache_volume("python_cache")
        return (
            dag.container()
            .from_("python:3.10-slim")
            .with_directory("/src", source)
            .with_mounted_cache("/src/.pytest_cache", python_cache)
            .with_workdir("/src")
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "git", "tree"])
            .with_exec(["pip", "install", "--upgrade", "pip"])
            .with_exec(["pip", "install", "hatch==1.7.0"])
            .with_exec(["pip", "install", "cookiecutter"])
            .with_exec(["pip", "install", "inquirer"])
            .with_exec(["pip", "install", "pytest"])
        )

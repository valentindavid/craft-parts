# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The parts lifecycle manager."""

from typing import Any, Dict, List

from craft_parts import sequencer
from craft_parts.actions import Action
from craft_parts.dirs import ProjectDirs
from craft_parts.infos import ProjectInfo
from craft_parts.parts import Part
from craft_parts.steps import Step


class LifecycleManager:
    """Coordinate the planning and execution of the parts lifecycle.

    The lifecycle manager determines the list of actions that needs be executed in
    order to obtain a tree of installed files from the specification on how to
    process its parts, and provides a mechanism to execute each of these actions.

    :param all_parts: A dictionary containing the parts specification according
        to the :ref:`parts schema<parts-schema>`. The format is compatible with the
        output generated by PyYAML's ``yaml.load``.
    :param application_name: A unique identifier for the application using Craft
        Parts. This string will be used as segregated directory path when creating
        persistent data that shouldn't be shared with other applications.
    :param build_packages: A list of additional build packages to install.
    :param work_dir: The toplevel directory for work directories. The current
        directory will be used if none is specified.
    :param arch: The architecture to build for. Defaults to the host system
        architecture.
    :param parallel_build_count: The maximum number of concurrent jobs to be
        used to build each part of this project.
    :param plugin_version: The plugin API version. Currently only ``v2`` is
        supported.
    :param custom_args: Any additional arguments that will be passed directly
        to :ref:`callbacks<callbacks>`.
    """

    def __init__(
        self,
        all_parts: Dict[str, Any],
        *,
        application_name: str,
        build_packages: List[str] = None,
        work_dir: str = ".",
        arch: str = "",
        parallel_build_count: int = 1,
        plugin_version: str = "v2",
        **custom_args,  # custom passthrough args
    ):
        # TODO: validate base_dir

        # TODO: validate parts schema

        # TODO: validate or slugify application name

        project_dirs = ProjectDirs(work_dir=work_dir)

        project_info = ProjectInfo(
            application_name=application_name,
            arch=arch,
            plugin_version=plugin_version,
            parallel_build_count=parallel_build_count,
            project_dirs=project_dirs,
            **custom_args,
        )

        parts_data = all_parts.get("parts", {})
        self._part_list = [
            Part(name, p, project_dirs=project_dirs) for name, p in parts_data.items()
        ]
        self._application_name = application_name
        self._target_arch = project_info.target_arch
        self._build_packages = build_packages
        self._sequencer = sequencer.Sequencer(
            part_list=self._part_list,
            project_info=project_info,
        )
        self._project_info = project_info

    @property
    def project_info(self) -> ProjectInfo:
        """Obtain information about this project."""
        return self._project_info

    def plan(self, target_step: Step, part_names: List[str] = None) -> List[Action]:
        """Obtain the list of actions to be executed given the target step and parts.

        :param target_step: The final step we want to reach.
        :param part_names: The list of parts to process. If not specified, all
            parts will be processed.
        :param update: Refresh the list of available packages.

        :return: The list of :class:`Action` objects that should be executed in
            order to reach the target step for the specified parts.
        """
        # TODO: verify if base packages changed

        actions = self._sequencer.plan(target_step, part_names)
        return actions

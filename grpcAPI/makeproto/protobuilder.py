from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from makeproto.map_to_block2 import cls_to_blocks
from makeproto.template_models import NO_PACKAGE, Block, ProtoBlocks
from makeproto.template_render import render_protofile


@dataclass
class Protobuilder:

    packs: Dict[Union[str, object], ProtoBlocks] = field(
        default_factory=dict[Union[str, object], ProtoBlocks]
    )

    def _get_protoblock(
        self, protofile: str, package: Union[str, object]
    ) -> ProtoBlocks:
        return self.packs.get(
            package, ProtoBlocks(protofile=protofile, package=package)
        )

    def add_service(self, service: Block) -> None:

        package = service.package or NO_PACKAGE

        protoblocks = self._get_protoblock(service.protofile, package)
        protoblocks.blocks.append(service)

        requests: List[type[Any]] = [m.request_type for m in service.fields]
        responses: List[type[Any]] = [m.response_type for m in service.fields]

        classes: set[type[Any]] = set(requests) | set(responses)

        blocks: set[Block] = set()
        for cls in classes:
            msgs = cls_to_blocks(cls)
            blocks.update(msgs)

        for block in blocks:
            msgblocks = self._get_protoblock(block.protofile, block.package)
            msgblocks.blocks.append(block)

    def render(self) -> Dict[Union[str, object], str]:

        rendered: Dict[Union[str, object], str] = {}

        for filename, file in self.packs.items():
            proto_str = render_protofile(file)
            rendered[filename] = proto_str

        return rendered

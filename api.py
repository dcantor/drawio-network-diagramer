"""
api.py — FastAPI backend for the network diagram generator.

Run with: uvicorn api:app --reload
"""

import ipaddress
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from leaf_spine import build_diagram

app = FastAPI(title="Network Diagram Generator")

app.mount("/static", StaticFiles(directory="static"), name="static")


class DiagramRequest(BaseModel):
    spines:            int = Field(ge=1, le=20)
    leaves:            int = Field(ge=1, le=40)
    borders:           int = Field(default=0, ge=0, le=10)
    wan:               int = Field(default=0, ge=0, le=10)
    super_spines:      int = Field(default=0, ge=0, le=10)
    fabrics:           int = Field(default=1, ge=1, le=10)
    vendor:            Literal["cisco", "arista"] = "cisco"
    include_firewalls: bool = True
    include_lbs:       bool = True
    include_dns:       bool = False
    include_ntp:       bool = False
    mgmt_pool:         str | None = None
    vlan_map:          str | None = None
    filename:          str = Field(default="leaf_spine", max_length=128)

    @model_validator(mode="after")
    def validate(self):
        if self.fabrics > 1 and self.super_spines == 0:
            raise ValueError("fabrics requires super_spines to be set")
        if self.mgmt_pool:
            try:
                ipaddress.ip_network(self.mgmt_pool, strict=False)
            except ValueError:
                raise ValueError(f"Invalid subnet: {self.mgmt_pool}")
        name = self.filename.strip().removesuffix(".drawio") or "leaf_spine"
        self.filename = "".join(c for c in name if c.isalnum() or c in "-_ ") or "leaf_spine"
        return self


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/generate")
def generate(req: DiagramRequest):
    try:
        diagram = build_diagram(
            req.spines, req.leaves, req.borders, req.wan,
            req.super_spines, req.fabrics, req.vendor,
            req.include_firewalls, req.include_lbs, req.include_dns, req.include_ntp,
            req.mgmt_pool, req.vlan_map,
        )
        xml_str = diagram.to_xml()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{req.filename}.drawio"'},
    )


from app.models import BitviewVideoListing
from fastapi import HTTPException

import requests
import config
import json
import time

class BitviewAPI:
    def __init__(
        self,
        endpoint: str,
        username: str,
        cloudflare_solver: str | None = None
    ) -> None:
        self.cloudflare_solver = cloudflare_solver
        self.endpoint = endpoint
        self.username = username
        
        self.last_response: BitviewVideoListing | None = None
        self.last_response_time: float | None = None
        self.last_response_ttl = 60
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"osuTitanic/keel ({config.DOMAIN_NAME})"
        })

    @property
    def cloudflare_session_missing(self) -> bool:
        if not self.cloudflare_solver:
            # We assume that cloudflare is not being used
            return False

        return "cf_clearance" not in self.session.cookies

    def fetch_videos(self) -> BitviewVideoListing:
        last_response_delta = (
            time.time() - self.last_response_time
            if self.last_response_time else 0
        )

        if self.last_response and last_response_delta < self.last_response_ttl:
            # Use cached response
            return self.last_response

        if self.cloudflare_session_missing:
            # Initialize cloudflare session
            return self.update_cloudflare_session()

        response = self.session.get(
            self.endpoint,
            params={"username": self.username}
        )

        if response.status_code == 403 and self.cloudflare_solver:
            # Our cloudflare session expired, try to update it
            return self.update_cloudflare_session()

        if response.status_code != 200:
            raise HTTPException(502, "Failed to fetch bitview videos.")

        self.last_response = response.json()
        self.last_response_time = time.time()
        return self.last_response

    def update_cloudflare_session(self) -> BitviewVideoListing:
        if not self.cloudflare_solver:
            return

        # NOTE: This requires a FlareSolverr instance to be running
        # https://github.com/FlareSolverr/FlareSolverr
        response = self.session.post(
            self.cloudflare_solver,
            json={
                "cmd": "request.get",
                "url": f"{self.endpoint}?username={self.username}",
                "maxTimeout": 60000
            },
            headers={
                "Content-Type": "application/json"
            }
        )

        if response.status_code != 200:
            raise HTTPException(502, "Failed to bypass cloudflare protection.")

        data = response.json()
        response_useragent = data["solution"]["userAgent"]
        response_cookies = data["solution"]["cookies"]

        # Update session headers and cookies
        self.session.headers.update({
            "User-Agent": response_useragent
        })

        for cookie in response_cookies:
            self.session.cookies.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain'),
                path=cookie.get('path'),
                expires=cookie.get('expiry'),
                secure=cookie.get('secure', False)
            )

        # For some reason, this can contain HTML, so we'll try to extract the JSON part
        response_json = data["solution"]["response"]
        response_json = response_json[response_json.index('{'):response_json.rindex('}')+1]

        self.last_response = json.loads(response_json)
        self.last_response_time = time.time()
        return self.last_response

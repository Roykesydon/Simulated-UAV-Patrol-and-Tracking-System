import requests


class Om2mRequestSender:
    def __init__(self):
        self.session_dict = {}
        pass

    def _get_session(self, url):
        if url not in self.session_dict:
            self.session_dict[url] = requests.Session()
        return self.session_dict[url]

    def create_application(self, url, app_name, labels: dict, poa=None):
        headers = {
            "Content-Type": "application/xml;ty=2",
            "X-M2M-Origin": "admin:admin",
        }

        # labels = {"Type": "patrol-drone", "Category": "drone"}
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <m2m:ae xmlns:m2m="http://www.onem2m.org/xml/protocols" rn="{app_name}">
            <api>app-sensor</api>
            <lbl>{ " ".join([f"{key}/{value}" for key, value in labels.items()]) }</lbl>
            <rr>true</rr>
            {"<poa>" + poa + "</poa>" if poa else ""}
            </m2m:ae>"""

        session = self._get_session(url)
        response = session.post(url, headers=headers, data=body)

    def create_container(self, url, app_name, container_name):
        headers = {
            "Content-Type": "application/xml;ty=3",
            "X-M2M-Origin": "admin:admin",
        }
        # set mni = 10
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <m2m:cnt xmlns:m2m="http://www.onem2m.org/xml/protocols" rn="{container_name}">
            <mni>10</mni>
            </m2m:cnt>
            """

        session = self._get_session(url)
        response = session.post(url + "/" + app_name, headers=headers, data=body)

    def subscribe(
        self, url, app_name, container_name, notification_url, subscription_name
    ):
        headers = {
            "Content-Type": "application/xml;ty=23",
            "X-M2M-Origin": "admin:admin",
        }

        body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <m2m:sub xmlns:m2m="http://www.onem2m.org/xml/protocols" rn="{subscription_name}">
            <nu>{notification_url}</nu>
            <nct>2</nct>
            </m2m:sub>
            """

        session = self._get_session(url)
        response = session.post(
            url + "/" + app_name + "/" + container_name, headers=headers, data=body
        )

    def create_content_instance(self, url, app_name, container_name, content: dict):
        headers = {
            "Content-Type": "application/xml;ty=4",
            "X-M2M-Origin": "admin:admin",
        }

        body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <m2m:cin xmlns:m2m="http://www.onem2m.org/xml/protocols">
            <cnf>message</cnf>
            <con>&lt;obj&gt;
            {" ".join([f"&lt;str name=&quot;{key}&quot; val=&quot;{value}&quot;/&gt;" for key, value in content.items()])}
            &lt;/obj&gt;</con>
            </m2m:cin>
            """

        session = self._get_session(url)
        response = session.post(
            url + "/" + app_name + "/" + container_name, headers=headers, data=body
        )

    def get_latest_content_instance(self, url, app_name, container_name):
        headers = {
            "Accept": "application/json",
            "X-M2M-Origin": "admin:admin",
        }
        session = self._get_session(url)
        response = session.get(
            url + "/" + app_name + "/" + container_name + "/la", headers=headers
        )

        return response.json()

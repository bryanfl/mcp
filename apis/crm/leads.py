import requests
from datetime import datetime, timedelta
from token_crm import TokenClient
import re

import xml.etree.ElementTree as ET

def crmquery3(pageQueryNumber, pageQueryCookie, inicio, fin):
    return f"""leads?fetchXml=<?xml version="1.0" encoding="UTF-8"?>
    <fetch version="1.0" output-format="xml-platform"
    returntotalrecordcount="true"
    mapping="logical"
    page="{pageQueryNumber}"
    distinct="true" >
    {pageQueryCookie}
    <entity name="lead" >
    <attribute name="utp_client_id" />
    <attribute name="createdon" />
    <attribute name="emailaddress1" />
    <attribute name="firstname" />
    <attribute name="lastname" />
    <attribute name="mobilephone" />
    <attribute name="onetoone_nro" />
    <attribute name="statecode" />
    <attribute name="statuscode" />
    <attribute name="leadid" />
    <attribute name="address1_line1" />
    <attribute name="utp_sub_grado" />
    <attribute name="utp_utm_term" />
    <attribute name="utp_nombre_campana_digital" />
    <attribute name="utp_id_campana_digital" />
    <attribute name="utp_utm_content" />
    <attribute name="utp_utm_source" />
    <link-entity name="product" from="productid" to="onetoone_producto" link-type="outer" alias="pro" >
    <attribute name="name" />
    <attribute name="onetoone_codigopeoplesoft" />
    </link-entity>
    <link-entity name="onetoone_sedeeducativa" from="onetoone_sedeeducativaid" to="onetoone_sededeseada" link-type="outer" alias="sed" >
    <attribute name="onetoone_name" />
    <attribute name="onetoone_codigo" />
    </link-entity>
    <link-entity name="onetoone_detallefuenteorigen" from="onetoone_detallefuenteorigenid" to="onetoone_detallefuenteorigen" link-type="inner" alias="dfu" >
    <attribute name="onetoone_name" />
    </link-entity>
    <link-entity name="onetoone_pais" from="onetoone_paisid" to="utp_pais_origen" link-type="outer" alias="pai" >
    <attribute name="onetoone_name" />
    </link-entity>
    <link-entity name="contact" from="originatingleadid" to="leadid" link-type="outer" >
    <link-entity name="opportunity" from="customerid" to="contactid" link-type="outer" alias="opor" >
    <attribute name="onetoone_pagodepostulacionpre" />
    <attribute name="onetoone_pagodematricula" />
    <attribute name="utp_fecha_pago_matricula" />
    <attribute name="utp_fecha_pago_inscripcion" />
    <link-entity name="onetoone_postulante" from="onetoone_oportunidad" to="opportunityid" link-type="outer" alias="pos">
    <attribute name="onetoone_dopagodepostulacionpre" />
    </link-entity>
    </link-entity>
    </link-entity>
    <filter type="and" >
    <condition attribute="createdon" operator="ge" value="{inicio}" />
    <condition attribute="createdon" operator="le" value="{fin}" />
    </filter>
    </entity>
    </fetch>"""

def getLeadsPaginados(crmApi, crmrequestheaders, inicio, fin, url=None, leads=None, valor_pagina=1):
    if leads is None:
        leads = []
    if url is None:
        url = f"{crmApi}{crmquery3(valor_pagina, '', inicio, fin)}"
    response = requests.get(url, headers=crmrequestheaders)
    if response.status_code != 200:
        raise Exception(f"{response.status_code}: {response.reason}")
    data = response.json()
    leads.extend(data.get('value', []))
    if data.get('@Microsoft.Dynamics.CRM.morerecords'):
        paging_cookie_xml = data['@Microsoft.Dynamics.CRM.fetchxmlpagingcookie']
        root = ET.fromstring(paging_cookie_xml)
        pagingcookie = root.attrib.get('pagingcookie', '')
        pageQueryNumber = valor_pagina + 1
        pageQueryCookie = pagingcookie
        return getLeadsPaginados(
            crmApi, crmrequestheaders, inicio, fin,
            url=f"{crmApi}{crmquery3(pageQueryNumber, pageQueryCookie, inicio, fin)}",
            leads=leads,
            valor_pagina=pageQueryNumber
        )
    else:
        return leads

def tokenLeads(inicio, fin):
    print(inicio)
    print(fin)
    crmApi = 'https://utp.api.crm2.dynamics.com/api/data/v9.2/'
    solicitudToken = TokenClient()
    responseSolicitudToken = solicitudToken.get_token()
    crmrequestheaders = {
        'Authorization': f"Bearer {responseSolicitudToken['access_token']}",
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'Prefer': 'odata.include-annotations=*'
    }
    leads = getLeadsPaginados(crmApi, crmrequestheaders, inicio, fin)
    regexTelefono = re.compile(r"\d{9}")
    regexEmail = re.compile(r"^[\w!#\$%&'\*\+\/\=\?\^`\{\|\}~\-]+(:?\.[\w!#\$%&'\*\+\/\=\?\^`\{\|\}~\-]+)*@(?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?$", re.I)
    LeadsHash = []
    for items in leads:
        if regexEmail.match(items.get('emailaddress1', '')) and regexTelefono.match(str(items.get('mobilephone', ''))):
            status_crm = ''
            pos_pago = items.get('pos.onetoone_dopagodepostulacionpre')
            opor_matricula = items.get('opor.onetoone_pagodematricula')
            statecode = items.get('statecode')
            if pos_pago is True:
                if opor_matricula is True:
                    status_crm = 'matriculado'
                elif opor_matricula is False:
                    status_crm = 'inscrito'
            elif pos_pago is False:
                status_crm = 'pago_generado'
            elif pos_pago is None:
                if statecode != 2:
                    status_crm = 'valido'
            LeadsHash.append({
                'detail_source': items.get("dfu.onetoone_name"),
                'phone': items.get('mobilephone'),
                'document': items.get('onetoone_nro'),
                'utm_campaign': items.get('utp_nombre_campana_digital'),
                'utm_content': items.get('utp_utm_content'),
                'status_crm': status_crm,
            })
    filtered = [
        item for item in LeadsHash
        if item and (
            ("facebook" in (item.get('detail_source') or '').lower()) or
            ("fb" in (item.get('detail_source') or '').lower())
        )
    ]
    
    return filtered
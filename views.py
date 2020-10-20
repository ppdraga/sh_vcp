import json
import asyncio
import aiomysql

from aiohttp import web, ClientSession
import aiohttp_jinja2

from settings import config
import settings


@aiohttp_jinja2.template('index.html')
async def index(request):
    if request.method == 'GET':
        srv_data = {}
        if request.query.get('Search'):
            # Get data from Search
            servers = request.query['Search'].split(' ')
        elif request.query.get('ServerList'):
            # Get data from textarea
            servers = request.query.get('ServerList').split('\r\n')
        else:
            # Get data from MySQL
            if settings.USE_DATASOURCE:
                try:
                    conn = await aiomysql.connect(**config.get('DATA_SOURCE'), loop=asyncio.get_event_loop())
                    cur = await conn.cursor()
                    await cur.execute("SELECT hostname FROM cdn_server")
                    response = await cur.fetchall()
                    servers = []
                    for row in response:
                        servers.append(row[0])
                    await cur.close()
                    conn.close()
                except Exception as e:
                    return {'srv_data': {}, 'error': str(e)}

        if servers:
            await get_server_data(servers, srv_data)

            srv_data = sorted(srv_data.values(), key=lambda x: (x.get('error',''), x.get('hostname')))
            print(srv_data)
            return {'srv_data': srv_data, }

    return {'srv_data': {}}


async def get_server_data(servers, srv_data):
    tasks = []
    async with ClientSession() as session:
        for srv in servers:
            if srv:
                url = 'http://{0}/storehouse_infos/'.format(srv)
                task = asyncio.create_task(fetch_content(url, session, srv, srv_data))
                tasks.append(task)

        await asyncio.gather(*tasks)


async def fetch_content(url, session, srv, srv_data):
    try:
        async with session.get(url, allow_redirects=True) as response:
            binary_data = await response.read()
            try:
                json_data = json.loads(binary_data)
                json_data['hostname'] = srv
                print(json_data)
                srv_data[srv] = json_data
            except:
                srv_data[srv] = {'error': 'Data not valid or API is down!', 'hostname': srv}
    except Exception as e:
        srv_data[srv] = {'error': str(e), 'hostname': srv}

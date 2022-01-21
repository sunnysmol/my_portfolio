from types import new_class
import streamlit as st
import requests
import json
import pandas as pd
import numpy as np
from itertools import cycle
from pprint import pprint
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from streamlit_autorefresh import st_autorefresh

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
count = st_autorefresh(interval=200000, key="fizzbuzzcounter")
addresses = ["0xC844bB1D41C052d73f002080F19C17C9E5545291","0x76844D2Fc304c9a42602E01b7774354e1d80Be1c","0x579AB4758d489AC6315661151f6f016AcdE917b6"]
# add = st.text_input('Add Your Wallet Address', 'wallet address')
# if st.button('Add Address'):
     
#      if add:
#          addresses.append(add)
# else:
#      st.write('Enter Address')
def buildFloorQuery():
    query = gql(
        f"""
        {{
        collections {{
            id
            address
            name
            totalListings
            floorPrice
        }}
        }}
        """
        )
    return query

def getSmolFloorPrice(collection):
    transport = AIOHTTPTransport(url="https://api.thegraph.com/subgraphs/name/wyze/treasure-marketplace")

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)
    result = client.execute(buildFloorQuery())
    pprint(result)
    smolbrains = [obj for obj in result['collections'] if(obj['name'] == collection)]
    floor = int(smolbrains[0]['floorPrice'])/1000000000000000000
    #print(f"floor is {floor}")
    return floor

def getPriceGraph(ticker):
    query = gql(
        f"""
        {{
        pairs(where:{{name:"{ticker}-USDT"}}){{
            name
            token1Price
            }}
        }}
        """
        )
    transport = AIOHTTPTransport(url="https://api.thegraph.com/subgraphs/name/sushiswap/arbitrum-exchange")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    result = client.execute(query)
    pprint(result)
    return(round(float(result["pairs"][1]["token1Price"]),3))

def getEthPrice():
    url = 'https://deep-index.moralis.io/api/v2/erc20/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2/price?chain=eth'
    try:
        request = requests.get(url,headers={"x-api-key":"NDAdoHJ977HcjeKNgW8EZmHc5tyAXGqT1Awgi344FiOnYeOwjLe11xw9KSedPCk3"})
        data = request.json()
    except Exception as e:
        data = []
    print(data)
    return round(data['usdPrice'],2)  

def getHistoricalPortfolioValue(address,chain):

    url = f"https://api.covalenthq.com/v1/{chain}/address/{address}/portfolio_v2/?quote-currency=USD&format=JSON&key=ckey_78290656a6ca426fa748bdcd41b"
    try:
        request = requests.get(url)
        data = request.json()
    except Exception as e:
        data = []
    
    if data["items"]:
        return data["items"]
    

def getTransactions(address,chain):
    url = f"https://api.covalenthq.com/v1/{chain}/address/{address}/transactions_v2/?quote-currency=USD&format=JSON&block-signed-at-asc=false&no-logs=false&key=ckey_78290656a6ca426fa748bdcd41b"
    request = requests.get(url)
    data = request.json()
    return data["items"]

def allAddressValue(wallets):
    total = 0
    for address in wallets:
        request = requests.get(f'https://openapi.debank.com/v1/user/total_balance?id={address}')
        data = request.json()
        total = round(data['total_usd_value']) + total
    
    return total

def getNFTFloor(collection_slug):
    url = f'https://api.opensea.io/api/v1/collection/{collection_slug}/stats'

    headers = {"Accept": "application/json"}

    response = requests.request("GET", url, headers=headers)
    data = response.json()
    return data['stats']['floor_price']

def getNFTSOpensea(address):
    url = f"https://api.opensea.io/api/v1/collections?asset_owner={address}&offset=0&limit=300"

    headers = {"Accept": "application/json"}

    response = requests.request("GET", url, headers=headers)
    data = response.json()
    return data

def showWallets(addresses):
    for address in addresses:
        with st.expander(address):
            request = requests.get(f'https://openapi.debank.com/v1/user/total_balance?id={address}')
            data = request.json()
        
            st.metric("Total Portfolio",f"${round(data['total_usd_value'])}")
            cols = cycle(st.columns(3)) # st.columns here since it is out of beta at the time I'm writing this
            for idx, chain in enumerate(data["chain_list"]):
                if chain["usd_value"] > 0:
                    next(cols).metric(chain["name"], f'${round(chain["usd_value"])}')
#Total Portfolio
totoal_portfolio = st.container()

kpi1,kpi2,kpi3=st.columns(3)
kpi4,kpi5,kpi6=st.columns(3)


def showNftTable():
    pprint(getNFTSOpensea(addresses[0])[0])
    nft_df = pd.DataFrame(getNFTSOpensea(addresses[0]))
    new_df = nft_df[['slug','owned_asset_count']]
    pprint(new_df)
    floor_value = []
    total_value = []
    for row in new_df['slug']:
        f = getNFTFloor(row)
        floor_value.append(f)
        

    new_df['floor_value'] = floor_value
#print(new_df)
    new_df["Total Value"] = new_df['owned_asset_count'] * new_df['floor_value']
    st.dataframe(new_df)
    return new_df

magic_usd = getPriceGraph('MAGIC')
eth_usd = getEthPrice()

st.title("NFTs")
new_df = showNftTable()
#print(new_df)
#print(new_df['Total Value'].sum())#sum
kpi1.metric(label="NFT Value in ETH", value=new_df['Total Value'].sum())
kpi2.metric(label="NFT Value in USD", value=f"${round(new_df['Total Value'].sum() * eth_usd,2)}")
kpi5.metric(label="Magic Price", value=f"${magic_usd}")

#smolverse 
smol_brains_floor = getSmolFloorPrice("Smol Brains")
smol_boadies_floor = getSmolFloorPrice("Smol Bodies")
magic_price = magic_usd
total_smols_value = round(float((smol_brains_floor*magic_price)+(smol_boadies_floor*magic_price)),2)
kpi3.metric(label="Smolverse Value USD", value=f"${total_smols_value}")
totoal_portfolio.title(f"Portfolio:   ${round((allAddressValue(addresses))+ new_df['Total Value'].sum() * eth_usd,2)+total_smols_value}")
#nft_data = getNFTFloor("Monsterbuds")
#pprint(nft_data)



# workingdata = getHistoricalPortfolioValue(addresses[0],1)
# df_holdings = pd.json_normalize(workingdata[0],record_path=[['holdings']])
# df_holdings.reset_index(drop=True, inplace=True)
# df = pd.DataFrame(workingdata)
# finadf = [df["contract_name"]]
# print(df)
# #st.dataframe(df)
# #st.dataframe(df_holdings)
# chart_data = pd.DataFrame(
#      np.random.randn(20, 3),
#      columns=['a', 'b', 'c'])
# cd = df_holdings[['close.quote','timestamp']].astype(str)
# cd.set_index('timestamp', inplace=True)

#st.dataframe(cd)
#st.line_chart(data=cd,width=400, height=500, use_container_width=True)


st.title("Wallets")
showWallets(addresses)


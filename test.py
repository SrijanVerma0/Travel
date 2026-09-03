from tools.tavily_tool import tavily_search
from tools.aviation_tool import flight_search

print("=== Testing Flight Search ===")
flight_res = flight_search("plan a trip from ind to singapore")
print(flight_res)

# print("\n=== Testing Tavily Search ===")
# tavily_res = tavily_search("top 3 5 star hotels of india")
# print(tavily_res)
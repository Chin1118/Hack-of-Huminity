from supabase import create_client
from backend.config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# # 2. Test the connection
# def test_supabase_connection():
#     try:
#         # Attempt a very lightweight query 
#         # (Fetching just 1 row from a table you know exists)
#         response = supabase.table("Testing").select("*").limit(1).execute()
        
#         print("✅ Successfully connected to Supabase!")
#         # Optional: print(response.data) to see the fetched row
#         return True
        
#     except Exception as e:
#         print(f"❌ Failed to connect to Supabase.")
#         print(f"Error details: {e}")
#         return False

# if __name__ == "__main__": 
#     test_supabase_connection()
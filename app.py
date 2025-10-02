from flask import Flask
from flask_mysqldb import MySQL
from flask import jsonify, request
from trie import Trie
from bst import BST
from datetime import datetime
import traceback
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  
app.config['MYSQL_DB'] = 'carbon_tracker'

mysql = MySQL(app)
eco_trie = Trie()

# Emission calculation function
def calculate_emissions(travel_km: float, energy_kwh: float, food_type: str, transport_mode: str):
    # Transport factors dictionary 
    TRANSPORT_FACTORS = {
        'car': 0.20,  # kgCO2 per km (default)
        'bus': 0.08,       
        'train': 0.04,     
        'flight': 0.35,    
        'bike': 0.0,       
        'default': 0.20    
    }

    ENERGY_FACTOR = 0.5  # kgCO2 per kWh
    FOOD_FACTORS = {
        'meat': 5.0,  # kgCO2 per day (default)
        'dairy': 3.0,    
        'vegetarian': 1.5, 
        'vegan': 1.0     
    }
    
    mode_factor = TRANSPORT_FACTORS.get(transport_mode.lower(), TRANSPORT_FACTORS['default'])
    travel_em = travel_km * mode_factor
    energy_em = energy_kwh * ENERGY_FACTOR
    food_em = FOOD_FACTORS.get(food_type.lower(), FOOD_FACTORS['meat'])  # Default to meat factor
    
    # Total Emission
    total_em = travel_em + energy_em + food_em
    
    return travel_em, energy_em, food_em, total_em

@app.route('/api/add_footprint', methods=['POST'])
def add_footprint_record():
    cur = None
    try:
        data = request.get_json()
        print("DEBUG: Incoming Data:", data)  

        # Extract Raw Input Data
        user_id = data.get('uid')
        record_date = data.get('rdate') 
        travel_km = float(data.get('travel_km', 0.0))
        energy_kwh = float(data.get('energy_kwh', 0.0))
        food_type = data.get('food_type', 'meat')
        transport_mode = data.get('transport_mode', 'car')

        # Validation
        if not user_id or not record_date:
            return jsonify({"message": "Missing required fields (uid, rdate) in the request body."}), 400
        if travel_km < 0 or energy_kwh < 0:
            return jsonify({"message": "travel_km and energy_kwh must be non-negative."}), 400

        # Calculate Emissions
        travel_em, energy_em, food_em, total_em = calculate_emissions(
            travel_km, energy_kwh, food_type, transport_mode
        )
        print("DEBUG: Total Emission Calculated:", total_em) 

        # Insert Raw Inputs + Calculated Total + transport_mode into MySQL
        # Order matches your schema: total_em before transport_mode
        cur = mysql.connection.cursor()
        query = """
            INSERT INTO fp_records (uid, rdate, travel_km, energy_kwh, food_type, total_em, transport_mode)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (
            user_id, 
            record_date, 
            travel_km,
            energy_kwh,
            food_type,
            round(total_em, 2),  # total_em before transport_mode to match schema order
            transport_mode
        ))
        
        mysql.connection.commit()

        return jsonify({
            "message": "Footprint record successfully calculated and inserted.",
            "total_footprint": round(total_em, 2),
            "breakdown_calculated": {
                "travel_em": round(travel_em, 2),
                "energy_em": round(energy_em, 2),
                "food_em": round(food_em, 2)
            }
        }), 201

    except Exception as e:
        if cur:
            cur.close()
        app.logger.error(f"Error in add_footprint_record: {traceback.format_exc()}")
        return jsonify({"message": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        if cur:
            cur.close()

# Trie inserts for eco-tips (fixed missing comma in "lamb")
eco_trie.insert("car", [
    "Take public transit or carpool!",
    "Work from home if possible.",
    "Consider an electric vehicle."
])
eco_trie.insert("bike", [
    "Use a bicycle for short trips.",
    "Combine errands to reduce trips."
])
eco_trie.insert("plane", [  # Note: Frontend uses "flight"—consider aligning if needed
    "Offset your flight's carbon footprint.",
    "Choose direct flights to reduce emissions."
])

# Food
eco_trie.insert("lamb", [
    "Try a plant-based meal.",
    "Reduce portion sizes of red meat,",  # Fixed: Added comma
    "Switch to chicken or fish."
])
eco_trie.insert("dairy", [
    "Use plant-based milk alternatives.",
    "Buy local dairy products to reduce transport emissions."
])
eco_trie.insert("packaged_food", [
    "Buy fresh, local produce.",
    "Avoid single-use packaging."
])

# Energy
eco_trie.insert("lights", [
    "Switch to LED bulbs.",
    "Turn off lights when not in use."
])
eco_trie.insert("ac", [
    "Set AC to a higher temperature.",
    "Use fans or natural ventilation."
])

# Waste
eco_trie.insert("plastic_bags", [
    "Use reusable bags.",
    "Recycle or compost when possible."
])
eco_trie.insert("single_use_straws", [
    "Switch to metal or bamboo straws."
])
eco_trie.insert("bottles", [
    "Use reusable water bottles.",
    "Recycle plastic bottles."
])

# Water
eco_trie.insert("shower", [
    "Take shorter showers.",
    "Install water-efficient fittings."
])
eco_trie.insert("tap", [
    "Turn off the tap while brushing or washing dishes."
])

# Test DB connection
@app.route('/')
def test_db(): 
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES;")
        tables = cur.fetchall()
        return f"Tables in carbon_tracker DB: {tables}"
    except Exception as e:
        return f"Error connecting to DB: {str(e)}", 500
    finally:
        if cur:
            cur.close()

@app.route('/api/footprints', methods=['GET'])
def get_all_footprints():
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM fp_records;")
        records = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        footprints = []
        for record in records:
            footprints.append(dict(zip(columns, record))) 
        return jsonify(footprints)
    except Exception as e:
        app.logger.error(f"Error in get_all_footprints: {traceback.format_exc()}")
        return jsonify({"message": f"Error fetching footprints: {str(e)}"}), 500
    finally:
        if cur:
            cur.close()

@app.route('/api/suggest', methods=['GET'])
def get_recommendation():
    prefix = request.args.get('prefix', '').lower()
    
    suggestions = eco_trie.search(prefix)
    
    if suggestions:
        return jsonify({
            "prefix": prefix,
            "recommendations": suggestions,
            "message": "Suggestions retrieved using custom Trie structure."
        })
    else:
        return jsonify({
            "prefix": prefix,
            "recommendations": [],
            "message": "No specific recommendations found for this item."
        })

@app.route('/api/trend/<int:user_id>', methods=['GET'])
def get_user_trend(user_id):
    cur = None
    try:
        cur = mysql.connection.cursor()
        # Fetch including transport_mode for accurate recalculation
        cur.execute("""
            SELECT rdate, travel_km, energy_kwh, food_type, transport_mode 
            FROM fp_records 
            WHERE uid = %s 
            ORDER BY rdate ASC
        """, (user_id,))
        records = cur.fetchall()

        if not records:
            return jsonify({"message": f"No historical data found for user ID {user_id}."}), 404

        # Insert into BST with recalculated total_em using actual transport_mode
        footprint_tree = BST()
        for date_obj, travel_km, energy_kwh, food_type, transport_mode in records:
            _, _, _, total_em = calculate_emissions(
                float(travel_km), float(energy_kwh), food_type, transport_mode
            )
            footprint_tree.insert(date_obj, round(total_em, 2)) 
        
        # Inorder traversal for sorted data (oldest to newest)
        sorted_records = footprint_tree.get_inorder_traversal() 
        
        return jsonify({
            "user_id": user_id,
            "trend_data": sorted_records,
            "message": "Data retrieved using custom BST Inorder Traversal (Search Algorithm)."
        })
    except Exception as e:
        app.logger.error(f"Error in get_user_trend: {traceback.format_exc()}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    finally:
        if cur:
            cur.close()

def bubble_sort(activities):
    n = len(activities)
    for i in range(n-1):
        for j in range(0, n-i-1):
            if activities[j][1] < activities[j+1][1]:
                activities[j], activities[j+1] = activities[j+1], activities[j]
    return activities

@app.route('/api/rank_impact/<int:user_id>/<string:date>', methods=['GET'])
def rank_impact(user_id, date):
    cur = None
    try:
        cur = mysql.connection.cursor()
        
        # Query for the specific date (now fetches transport_mode)
        query = """
            SELECT travel_km, energy_kwh, food_type, transport_mode
            FROM fp_records
            WHERE uid = %s AND rdate = %s
            LIMIT 1;
        """
        cur.execute(query, (user_id, date))
        record = cur.fetchone()

        if not record:
            return jsonify({
                "message": f"No data found for user ID {user_id} on date {date}. Data retrieved but empty."
            }), 404 
        
        # Unpack record (transport_mode is fetched correctly)
        travel_km, energy_kwh, food_type, transport_mode = record
        
        # Calculate emissions using actual transport_mode
        travel_em, energy_em, food_em, _ = calculate_emissions(
            float(travel_km), 
            float(energy_kwh), 
            food_type, 
            transport_mode
        )

        # List of tuples for bubble sort (descending: highest to lowest)
        activities_impact = [
            ("Travel", round(travel_em, 2)),
            ("Energy", round(energy_em, 2)),
            ("Food", round(food_em, 2))
        ] 
        
        ranked_activities = bubble_sort(activities_impact)
        
        return jsonify({
            "user_id": user_id,
            "date": date,
            "ranking_method": "Custom Bubble Sort Algorithm (Calculated Breakdown)",
            "ranked_activities": ranked_activities,
            "message": "Data retrieved and activities ranked successfully for the selected date."
        })
    
    except Exception as e:
        app.logger.error(f"Error in rank_impact: {traceback.format_exc()}")
        return jsonify({
            "message": f"Error processing impact ranking: {str(e)}"
        }), 500
    finally:
        if cur:
            cur.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# Kilterboard Hold Usage Analysis 🧗

Backend API for analyzing hold usage on the Kilterboard. U

Uses FastAPI for the web framework, SQLite Cloud for database, and Render for deployment.

## Setup

### 1. Clone the repository

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Unix/MacOS
(venv) pip install -r requirements.txt
```

### 3. Set up the database

#### Local

Refactor the `src/db.py` file to use a local SQLite database. Use [BoardLib](https://github.com/lemeryfertitta/BoardLib) to get a copy of the kilter database.

#### SQLite Cloud

_--Left as an exercise to the reader--_

### 4. Run the application

```bash
uvicorn src.main:app --reload
```

# Kilterboard Heatmap API Documentation

## Base URL

```
https://<api-domain>.com/api/v1
```

## Endpoints

### Get Heatmap Data

Generate a heatmap visualization of hold usage based on specified criteria.

```http
POST /heatmap
```

#### Request Body

```json
{
  "min_grade": 15.0,
  "max_grade": 20.0,
  "angle": 40,
  "hold_type": "hands",
  "min_ascents": 10
}
```

| Parameter   | Type    | Required | Description                                          | Constraints                                                                  |
| ----------- | ------- | -------- | ---------------------------------------------------- | ---------------------------------------------------------------------------- |
| min_grade   | float   | Yes      | Minimum grade for climbs to include                  | 10.0 to 33.0                                                                 |
| max_grade   | float   | Yes      | Maximum grade for climbs to include                  | 10.0 to 33.0                                                                 |
| angle       | integer | Yes      | Wall angle in degrees                                | 0 to 70, must be multiple of 5                                               |
| hold_type   | string  | No       | Type of holds to analyze                             | Must be one of: "all", "hands", "start", "finish", "foot". Defaults to "all" |
| min_ascents | integer | No       | Minimum number of ascents for a climb to be included | Must be ≥ 0. Defaults to 10                                                  |

#### Response

```json
{
  "holds": [
    {
      "x": 4,
      "y": 8,
      "frequency": 150,
      "frequency_norm": 0.75
    }
    // ... more holds
  ],
  "metadata": {
    "min_grade": 15,
    "max_grade": 20,
    "angle": 40,
    "hold_type": "hands",
    "total_climbs": 245,
    "invalid_climbs": 2,
    "valid_climbs": 243,
    "total_holds": 476,
    "max_frequency": 200
  }
}
```

| Field                   | Type    | Description                                                  |
| ----------------------- | ------- | ------------------------------------------------------------ |
| holds                   | array   | List of holds and their usage frequencies                    |
| holds[].x               | integer | X-coordinate of the hold                                     |
| holds[].y               | integer | Y-coordinate of the hold                                     |
| holds[].frequency       | integer | Raw count of how many times this hold was used               |
| holds[].frequency_norm  | float   | Normalized frequency (0.0 to 1.0) relative to most used hold |
| metadata                | object  | Statistics about the dataset                                 |
| metadata.min_grade      | integer | Minimum grade used in query                                  |
| metadata.max_grade      | integer | Maximum grade used in query                                  |
| metadata.angle          | integer | Wall angle used in query                                     |
| metadata.hold_type      | string  | Hold type filter used in query                               |
| metadata.total_climbs   | integer | Total number of climbs matching grade/angle criteria         |
| metadata.invalid_climbs | integer | Number of climbs with invalid frame data                     |
| metadata.valid_climbs   | integer | Number of climbs successfully analyzed                       |
| metadata.total_holds    | integer | Total number of unique holds used                            |
| metadata.max_frequency  | integer | Highest frequency count for any single hold                  |

### Get Available Angles

Retrieve list of all available wall angles in the dataset.

```http
GET /angles
```

#### Response

```json
[20, 25, 30, 35, 40, 45, 50, 55, 60]
```

Returns an array of integers representing available wall angles in degrees.

### Get Grade Information

Retrieve grade mapping information for the system.

```http
GET /grades
```

#### Response

```json
[
  {
    "difficulty": 10,
    "boulder_name": "V0",
    "route_name": "5.10a"
  },
  {
    "difficulty": 11,
    "boulder_name": "V0+",
    "route_name": "5.10b"
  }
  // ... more grades
]
```

| Field        | Type    | Description                            |
| ------------ | ------- | -------------------------------------- |
| difficulty   | integer | Internal difficulty value (10-33)      |
| boulder_name | string  | Boulder grade in V-scale               |
| route_name   | string  | Route grade in Yosemite Decimal System |

## Error Responses

The API uses standard HTTP status codes:

- 200: Success
- 400: Bad Request (invalid parameters)
- 404: Not Found (no data matching criteria)
- 500: Internal Server Error

Error responses include a detail message:

```json
{
  "detail": "No climbs found matching criteria"
}
```

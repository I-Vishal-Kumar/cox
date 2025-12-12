#!/bin/bash

# Test the backendV2 API with business intelligence questions using curl
# This script tests all questions from the questions.txt file

BASE_URL="http://localhost:8001"
LOG_FILE="curl_test_results_$(date +%Y%m%d_%H%M%S).log"
TEMP_FILE="/tmp/bi_questions.json"

echo "🎯 BUSINESS INTELLIGENCE API TESTING WITH CURL" | tee "$LOG_FILE"
echo "=" | tee -a "$LOG_FILE"
echo "Testing backendV2 API server with real business questions" | tee -a "$LOG_FILE"
echo "Base URL: $BASE_URL" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check server health first
echo "🔍 Checking server health..." | tee -a "$LOG_FILE"
health_response=$(curl -s -w "HTTP_STATUS:%{http_code}" "$BASE_URL/health")
http_status=$(echo "$health_response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)

if [ "$http_status" = "200" ]; then
    echo "✅ Server is healthy and responding" | tee -a "$LOG_FILE"
else
    echo "❌ Server health check failed (HTTP $http_status)" | tee -a "$LOG_FILE"
    echo "💡 Make sure the API server is running on localhost:8001" | tee -a "$LOG_FILE"
    exit 1
fi

# Parse questions from JSON file
echo "" | tee -a "$LOG_FILE"
echo "📋 Loading business intelligence questions..." | tee -a "$LOG_FILE"

# Extract questions from the JSON file
python3 -c "
import json
import sys

try:
    with open('../backend/questions.txt', 'r') as f:
        data = json.load(f)
    
    questions = []
    for category_name, category_data in data.items():
        for question in category_data.get('questions', []):
            questions.append({
                'category': category_name,
                'question': question
            })
    
    with open('$TEMP_FILE', 'w') as f:
        json.dump(questions, f, indent=2)
    
    print(f'Loaded {len(questions)} questions from {len(data)} categories')
    
except Exception as e:
    print(f'Error loading questions: {e}')
    sys.exit(1)
" | tee -a "$LOG_FILE"

if [ ! -f "$TEMP_FILE" ]; then
    echo "❌ Failed to parse questions file" | tee -a "$LOG_FILE"
    exit 1
fi

# Initialize counters
total_questions=0
successful_queries=0
cache_hits=0
total_tokens=0
total_response_time=0

echo "" | tee -a "$LOG_FILE"
echo "🚀 Starting API tests..." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test each question
while IFS= read -r line; do
    if [[ "$line" =~ \"question\".*:.*\"(.*)\" ]]; then
        question=$(echo "$line" | sed 's/.*"question": *"\([^"]*\)".*/\1/')
        category=$(echo "$prev_line" | sed 's/.*"category": *"\([^"]*\)".*/\1/' 2>/dev/null || echo "unknown")
        
        if [ ! -z "$question" ] && [ "$question" != "question" ]; then
            ((total_questions++))
            
            echo "🔍 Question $total_questions: '$question'" | tee -a "$LOG_FILE"
            echo "   Category: $category" | tee -a "$LOG_FILE"
            
            # Create JSON payload
            payload=$(cat <<EOF
{
  "query": "$question",
  "options": {
    "include_charts": true
  }
}
EOF
)
            
            # Make API call with timing
            start_time=$(date +%s%3N)
            
            response=$(curl -s -w "\\nHTTP_STATUS:%{http_code}\\nTIME_TOTAL:%{time_total}" \\
                -H "Content-Type: application/json" \\
                -d "$payload" \\
                "$BASE_URL/api/query")
            
            end_time=$(date +%s%3N)
            response_time=$((end_time - start_time))
            total_response_time=$((total_response_time + response_time))
            
            # Extract HTTP status
            http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
            curl_time=$(echo "$response" | grep "TIME_TOTAL:" | cut -d: -f2)
            
            # Remove status lines from response
            json_response=$(echo "$response" | sed '/HTTP_STATUS:/d' | sed '/TIME_TOTAL:/d')
            
            if [ "$http_status" = "200" ]; then
                # Parse JSON response
                success=$(echo "$json_response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('true' if data.get('success', False) else 'false')
    print(f\"tokens:{data.get('metadata', {}).get('tokens_used', 0)}\")
    print(f\"data_points:{data.get('metadata', {}).get('data_points', 0)}\")
    print(f\"charts:{data.get('metadata', {}).get('chart_count', 0)}\")
    print(f\"cache_hit:{data.get('metadata', {}).get('cache_hit', False)}\")
    print(f\"source:{data.get('metadata', {}).get('source', 'unknown')}\")
    if 'ai_response' in data:
        print(f\"ai_response:{data['ai_response'][:100]}...\")
except:
    print('false')
    print('tokens:0')
    print('data_points:0')
    print('charts:0')
    print('cache_hit:false')
    print('source:error')
")
                
                if echo "$success" | head -1 | grep -q "true"; then
                    ((successful_queries++))
                    
                    # Extract metrics
                    tokens=$(echo "$success" | grep "tokens:" | cut -d: -f2)
                    data_points=$(echo "$success" | grep "data_points:" | cut -d: -f2)
                    charts=$(echo "$success" | grep "charts:" | cut -d: -f2)
                    cache_hit=$(echo "$success" | grep "cache_hit:" | cut -d: -f2)
                    source=$(echo "$success" | grep "source:" | cut -d: -f2)
                    ai_response=$(echo "$success" | grep "ai_response:" | cut -d: -f2-)
                    
                    total_tokens=$((total_tokens + tokens))
                    
                    if [ "$cache_hit" = "True" ] || [ "$cache_hit" = "true" ]; then
                        ((cache_hits++))
                    fi
                    
                    echo "   ✅ SUCCESS ($source)" | tee -a "$LOG_FILE"
                    echo "   Response time: ${response_time}ms" | tee -a "$LOG_FILE"
                    echo "   Tokens used: $tokens" | tee -a "$LOG_FILE"
                    echo "   Data points: $data_points" | tee -a "$LOG_FILE"
                    echo "   Charts: $charts" | tee -a "$LOG_FILE"
                    
                    if [ ! -z "$ai_response" ] && [ "$ai_response" != "ai_response:" ]; then
                        echo "   AI Response: $ai_response" | tee -a "$LOG_FILE"
                    fi
                else
                    echo "   ❌ FAILED: API returned success=false" | tee -a "$LOG_FILE"
                fi
            else
                echo "   ❌ FAILED: HTTP $http_status" | tee -a "$LOG_FILE"
                echo "   Response: $(echo "$json_response" | head -c 200)..." | tee -a "$LOG_FILE"
            fi
            
            echo "" | tee -a "$LOG_FILE"
            
            # Small delay between requests
            sleep 0.2
        fi
    fi
    prev_line="$line"
done < "$TEMP_FILE"

# Generate summary report
echo "=" | tee -a "$LOG_FILE"
echo "🎉 CURL TEST SUMMARY REPORT" | tee -a "$LOG_FILE"
echo "=" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

success_rate=0
cache_hit_rate=0
avg_tokens=0
avg_response_time=0

if [ $total_questions -gt 0 ]; then
    success_rate=$((successful_queries * 100 / total_questions))
    cache_hit_rate=$((cache_hits * 100 / total_questions))
    avg_tokens=$((total_tokens / total_questions))
    avg_response_time=$((total_response_time / total_questions))
fi

echo "📊 OVERALL RESULTS:" | tee -a "$LOG_FILE"
echo "   Total Questions Tested: $total_questions" | tee -a "$LOG_FILE"
echo "   Successful Responses: $successful_queries" | tee -a "$LOG_FILE"
echo "   Failed Responses: $((total_questions - successful_queries))" | tee -a "$LOG_FILE"
echo "   Success Rate: ${success_rate}%" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "⚡ PERFORMANCE METRICS:" | tee -a "$LOG_FILE"
echo "   Cache Hit Rate: ${cache_hit_rate}%" | tee -a "$LOG_FILE"
echo "   Total Tokens Used: $total_tokens" | tee -a "$LOG_FILE"
echo "   Average Tokens per Query: $avg_tokens" | tee -a "$LOG_FILE"
echo "   Zero-Token Queries: $cache_hits" | tee -a "$LOG_FILE"
echo "   Average Response Time: ${avg_response_time}ms" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "🎯 TOKEN OPTIMIZATION ANALYSIS:" | tee -a "$LOG_FILE"
if [ $cache_hit_rate -ge 80 ]; then
    echo "   🔥 EXCELLENT: ${cache_hit_rate}% cache hit rate!" | tee -a "$LOG_FILE"
    echo "   💰 Major cost savings achieved" | tee -a "$LOG_FILE"
elif [ $cache_hit_rate -ge 60 ]; then
    echo "   ✅ GOOD: ${cache_hit_rate}% cache hit rate" | tee -a "$LOG_FILE"
    echo "   💡 Room for optimization" | tee -a "$LOG_FILE"
else
    echo "   ⚠️  NEEDS IMPROVEMENT: ${cache_hit_rate}% cache hit rate" | tee -a "$LOG_FILE"
    echo "   🔧 Consider expanding cached patterns" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

if [ $success_rate -ge 80 ]; then
    echo "🎊 EXCELLENT PERFORMANCE!" | tee -a "$LOG_FILE"
    echo "   🚀 System ready for production deployment" | tee -a "$LOG_FILE"
    echo "   💼 Comprehensive BI question coverage achieved" | tee -a "$LOG_FILE"
elif [ $success_rate -ge 60 ]; then
    echo "✅ GOOD PERFORMANCE!" | tee -a "$LOG_FILE"
    echo "   📈 System handles most business questions well" | tee -a "$LOG_FILE"
    echo "   🔧 Minor optimizations recommended" | tee -a "$LOG_FILE"
else
    echo "⚠️  NEEDS ATTENTION!" | tee -a "$LOG_FILE"
    echo "   🔧 System requires optimization for better coverage" | tee -a "$LOG_FILE"
    echo "   📋 Review failed queries for pattern improvements" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "Completed at: $(date)" | tee -a "$LOG_FILE"
echo "📄 Full results logged to: $LOG_FILE" | tee -a "$LOG_FILE"

# Cleanup
rm -f "$TEMP_FILE"

echo ""
echo "🎉 Testing complete! Check $LOG_FILE for detailed results."
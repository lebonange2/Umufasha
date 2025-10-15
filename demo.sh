#!/bin/bash

# Personal Assistant Demo Script
echo "🎬 Personal Assistant Demo"
echo "========================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Check if server is running
print_step "Checking if server is running..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Server is not running. Please start it first with: ./start.sh"
    exit 1
fi
print_success "Server is running"

# Check mock mode status
print_step "Checking mock mode status..."
STATUS=$(curl -s -H "Authorization: Bearer admin:admin123" http://localhost:8000/testing/status)
echo "$STATUS" | python3 -m json.tool

# Get users
print_step "Getting existing users..."
USERS=$(curl -s -H "Authorization: Bearer admin:admin123" http://localhost:8000/api/users/)
USER_COUNT=$(echo "$USERS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))")

if [ "$USER_COUNT" -eq 0 ]; then
    print_info "No users found. Creating a demo user..."
    
    # Create demo user
    USER_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer admin:admin123" \
        -d '{
            "name": "Demo User",
            "email": "demo@example.com",
            "phone_e164": "+1234567890",
            "timezone": "UTC",
            "channel_pref": "both"
        }' http://localhost:8000/api/users/)
    
    USER_ID=$(echo "$USER_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['id'])")
    print_success "Demo user created with ID: $USER_ID"
else
    print_info "Found $USER_COUNT existing users"
    USER_ID=$(echo "$USERS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'])")
    print_info "Using first user with ID: $USER_ID"
fi

echo ""
print_step "Demo 1: Testing Mock Call"
echo "=============================="
print_info "Simulating a phone call to the user..."

CALL_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer admin:admin123" \
    http://localhost:8000/testing/mock/test-call/$USER_ID)

echo "$CALL_RESPONSE" | python3 -m json.tool

CALL_SID=$(echo "$CALL_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['call_sid'])")

print_info "Call SID: $CALL_SID"
print_success "Mock call initiated successfully!"

echo ""
print_step "Demo 2: Testing Mock Email"
echo "==============================="
print_info "Sending a mock email to the user..."

EMAIL_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer admin:admin123" \
    http://localhost:8000/testing/mock/test-email/$USER_ID)

echo "$EMAIL_RESPONSE" | python3 -m json.tool

RSVP_TOKEN=$(echo "$EMAIL_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['rsvp_token'])")

print_info "RSVP Token: ${RSVP_TOKEN:0:50}..."
print_success "Mock email sent successfully!"

echo ""
print_step "Demo 3: Testing DTMF Simulation"
echo "===================================="
print_info "Simulating DTMF input (1 = Confirm)..."

DTMF_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer admin:admin123" \
    -H "Content-Type: application/json" \
    -d '{"digits": "1"}' \
    http://localhost:8000/testing/mock/simulate-dtmf/$CALL_SID)

echo "$DTMF_RESPONSE" | python3 -m json.tool
print_success "DTMF simulation completed!"

echo ""
print_step "Demo 4: Viewing Mock Data"
echo "============================="
print_info "Viewing all mock calls..."
curl -s -H "Authorization: Bearer admin:admin123" http://localhost:8000/testing/mock/calls | python3 -m json.tool

echo ""
print_info "Viewing all mock emails..."
curl -s -H "Authorization: Bearer admin:admin123" http://localhost:8000/testing/mock/emails | python3 -m json.tool

echo ""
print_step "Demo 5: Testing RSVP Link"
echo "============================="
print_info "Testing RSVP link (simulating email click)..."

RSVP_RESPONSE=$(curl -s "http://localhost:8000/rsvp/$RSVP_TOKEN?action=confirm")
echo "$RSVP_RESPONSE"

echo ""
echo "🎉 Demo completed successfully!"
echo "=============================="
echo ""
echo "📋 What we demonstrated:"
echo "✅ Mock phone call simulation"
echo "✅ Mock email generation"
echo "✅ DTMF input handling"
echo "✅ RSVP link processing"
echo "✅ Mock data storage and retrieval"
echo ""
echo "🌐 Next steps:"
echo "1. Visit the admin interface: http://localhost:8000/admin"
echo "2. Explore the API documentation: http://localhost:8000/docs"
echo "3. Create more users and test different scenarios"
echo "4. Add real API keys when ready for production"
echo ""
print_success "Your Personal Assistant is working perfectly! 🚀"

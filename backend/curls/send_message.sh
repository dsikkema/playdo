#!/usr/bin/env bash

CONV_ID=6
MESSAGE="take a moment to celebrate with me. When I first started having conversations with you through this codebase, it was over a CLI app. Now, I've upgraded to a rest api. Right now I'm inside vim in my terminal writing a curl command to send this message to my server which will relay it to you. And you helped bring it about, too, by answering quite a few questions. Isn't the future profound?"

curl -vX POST "$_PLAYDO_URL/api/conversations/$CONV_ID/send_message" \
-H "Content-Type: application/json" \
-d "{
  \"message\": \"$MESSAGE\"
}"

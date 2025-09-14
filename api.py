#!/usr/bin/env python3
"""
FastAPI version of LinkFinder
Converts the original LinkFinder script into a REST API endpoint
"""

import re
import html
import jsbeautifier
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="LinkFinderAPI",
    description="API to discover endpoints and parameters in JavaScript files",
    version="1.0.0"
)

# Regex used (same as original LinkFinder)
regex_str = r"""

  (?:"|')                               # Start newline delimiter

  (
    ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path

    |

    ((?:/|\.\./|\./)                    # Start with /,../,./
    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
    [^"'><,;|()]{1,})                   # Rest of the characters can't be

    |

    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    [a-zA-Z0-9_\-/.]{1,}                # Resource name
    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

    |

    ([a-zA-Z0-9_\-/]{1,}/               # REST API (no extension) with /
    [a-zA-Z0-9_\-/]{3,}                 # Proper REST endpoints usually have 3+ chars
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

    |

    ([a-zA-Z0-9_\-]{1,}                 # filename
    \.(?:php|asp|aspx|jsp|json|
         action|html|js|txt|xml)        # . + extension
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

  )

  (?:"|')                               # End newline delimiter

"""

context_delimiter_str = "\n"


class LinkFinderRequest(BaseModel):
    """Request model for LinkFinder API"""
    content: str
    include_context: bool = True
    filter_regex: Optional[str] = None
    remove_duplicates: bool = True


class EndpointResult(BaseModel):
    """Model for individual endpoint result"""
    link: str
    context: Optional[str] = None


class LinkFinderResponse(BaseModel):
    """Response model for LinkFinder API"""
    endpoints: List[EndpointResult]
    total_count: int


def get_context(list_matches, content, include_delimiter=0, context_delimiter_str="\n"):
    """
    Parse Input
    list_matches:       list of tuple (link, start_index, end_index)
    content:            content to search for the context
    include_delimiter   Set 1 to include delimiter in context
    """
    items = []
    for m in list_matches:
        match_str = m[0]
        match_start = m[1]
        match_end = m[2]
        context_start_index = match_start
        context_end_index = match_end
        delimiter_len = len(context_delimiter_str)
        content_max_index = len(content) - 1

        while content[context_start_index] != context_delimiter_str and context_start_index > 0:
            context_start_index = context_start_index - 1

        while content[context_end_index] != context_delimiter_str and context_end_index < content_max_index:
            context_end_index = context_end_index + 1

        if include_delimiter:
            context = content[context_start_index: context_end_index]
        else:
            context = content[context_start_index + delimiter_len: context_end_index]

        item = {
            "link": match_str,
            "context": context
        }
        items.append(item)

    return items


def parser_file(content, regex_str, mode=1, more_regex=None, no_dup=1):
    """
    Parse Input
    content:    string of content to be searched
    regex_str:  string of regex (The link should be in the group(1))
    mode:       mode of parsing. Set 1 to include surrounding contexts in the result
    more_regex: string of regex to filter the result
    no_dup:     remove duplicated link (context is NOT counted)

    Return the list of ["link": link, "context": context]
    The context is optional if mode=1 is provided.
    """
    global context_delimiter_str

    if mode == 1:
        # Beautify
        if len(content) > 1000000:
            content = content.replace(";",";\r\n").replace(",",",\r\n")
        else:
            content = jsbeautifier.beautify(content)

    regex = re.compile(regex_str, re.VERBOSE)

    if mode == 1:
        all_matches = [(m.group(1), m.start(0), m.end(0)) for m in re.finditer(regex, content)]
        items = get_context(all_matches, content, context_delimiter_str=context_delimiter_str)
    else:
        items = [{"link": m.group(1)} for m in re.finditer(regex, content)]

    if no_dup:
        # Remove duplication
        all_links = set()
        no_dup_items = []
        for item in items:
            if item["link"] not in all_links:
                all_links.add(item["link"])
                no_dup_items.append(item)
        items = no_dup_items

    # Match Regex
    filtered_items = []
    for item in items:
        # Remove other capture groups from regex results
        if more_regex:
            if re.search(more_regex, item["link"]):
                filtered_items.append(item)
        else:
            filtered_items.append(item)

    return filtered_items


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information"""
    return {
        "status": "ok"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LinkFinderAPI"}


@app.post("/analyze", response_model=LinkFinderResponse)
async def analyze_javascript(request: LinkFinderRequest):
    """
    Analyze JavaScript content to find endpoints and parameters
    
    Args:
        request: LinkFinderRequest containing the JavaScript content and options
        
    Returns:
        LinkFinderResponse with found endpoints and their contexts
    """
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Determine mode based on include_context
        mode = 1 if request.include_context else 0
        
        # Parse the file content
        endpoints = parser_file(
            content=request.content,
            regex_str=regex_str,
            mode=mode,
            more_regex=request.filter_regex,
            no_dup=1 if request.remove_duplicates else 0
        )
        
        # Convert to response format
        endpoint_results = []
        for endpoint in endpoints:
            result = EndpointResult(
                link=endpoint["link"],
                context=endpoint.get("context") if request.include_context else None
            )
            endpoint_results.append(result)
        
        return LinkFinderResponse(
            endpoints=endpoint_results,
            total_count=len(endpoint_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9402)

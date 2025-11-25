"""
PyNext Example - Dynamic User Route

Demonstrates dynamic routing with path parameters.
"""

from pynext import page, div, h1, h2, p, a, span, get_params


# Simulated user database
USERS = {
    "1": {"name": "Alice Johnson", "email": "alice@example.com", "role": "Developer"},
    "42": {"name": "Bob Smith", "email": "bob@example.com", "role": "Designer"},
    "123": {"name": "Charlie Brown", "email": "charlie@example.com", "role": "Manager"},
}


@page(title="User Profile")
def user_profile(id: str = ""):
    """Dynamic user profile page."""
    # Get route params
    params = get_params()
    user_id = params.get("id", id)
    
    # Look up user
    user = USERS.get(user_id)
    
    if not user:
        return div(class_="container")[
            div(class_="nav-back")[
                a(href="/")["← Back to Home"]
            ],
            div(class_="error-card")[
                h1()["User Not Found"],
                p()[f"No user found with ID: {user_id}"],
                p()[
                    "Try one of these: ",
                    a(href="/users/1")["User 1"], ", ",
                    a(href="/users/42")["User 42"], ", ",
                    a(href="/users/123")["User 123"],
                ]
            ],
            USER_STYLES
        ]
    
    return div(class_="container")[
        div(class_="nav-back")[
            a(href="/")["← Back to Home"]
        ],
        
        div(class_="profile-card")[
            div(class_="avatar")[
                user["name"][0]  # First letter as avatar
            ],
            h1()[user["name"]],
            p(class_="role")[user["role"]],
            
            div(class_="details")[
                div(class_="detail-row")[
                    span(class_="label")["Email:"],
                    span(class_="value")[user["email"]]
                ],
                div(class_="detail-row")[
                    span(class_="label")["User ID:"],
                    span(class_="value")[user_id]
                ],
            ]
        ],
        
        div(class_="info-card")[
            h2()["About Dynamic Routes"],
            p()[
                "This page is rendered from ", 
                span(class_="code")["pages/users/[id].py"],
                ". The ", 
                span(class_="code")["[id]"], 
                " part captures the URL segment as a parameter."
            ],
            p()[
                "Current route: ",
                span(class_="code")[f"/users/{user_id}"]
            ],
        ],
        
        div(class_="other-users")[
            h2()["Other Users"],
            div(class_="user-links")[
                [
                    a(href=f"/users/{uid}", class_="user-link")[
                        span(class_="mini-avatar")[u["name"][0]],
                        u["name"]
                    ]
                    for uid, u in USERS.items()
                    if uid != user_id
                ]
            ]
        ],
        
        USER_STYLES
    ]


from pynext.core.html import Element
style = Element("style")

USER_STYLES = style()["""
.container {
    max-width: 600px;
    margin: 0 auto;
    padding: 40px 20px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.nav-back {
    margin-bottom: 32px;
}

.nav-back a {
    color: #6366f1;
    text-decoration: none;
    font-weight: 500;
}

.profile-card {
    background: white;
    padding: 32px;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    margin-bottom: 24px;
}

.avatar {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    font-size: 36px;
    font-weight: 700;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
}

.profile-card h1 {
    margin: 0 0 4px 0;
    color: #1f2937;
}

.role {
    color: #6b7280;
    margin: 0 0 24px 0;
}

.details {
    text-align: left;
    background: #f9fafb;
    padding: 16px;
    border-radius: 8px;
}

.detail-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #e5e7eb;
}

.detail-row:last-child {
    border-bottom: none;
}

.label {
    color: #6b7280;
    font-weight: 500;
}

.value {
    color: #1f2937;
}

.info-card, .other-users {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 24px;
}

.info-card h2, .other-users h2 {
    margin: 0 0 16px 0;
    font-size: 18px;
    color: #1f2937;
}

.info-card p {
    color: #4b5563;
    margin: 0 0 12px 0;
    line-height: 1.6;
}

.code {
    background: #e5e7eb;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 14px;
}

.user-links {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.user-link {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: #f3f4f6;
    border-radius: 8px;
    text-decoration: none;
    color: #1f2937;
    transition: background 0.2s;
}

.user-link:hover {
    background: #e5e7eb;
}

.mini-avatar {
    width: 28px;
    height: 28px;
    background: #6366f1;
    color: white;
    font-size: 14px;
    font-weight: 600;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.error-card {
    background: #fef2f2;
    border: 1px solid #fecaca;
    padding: 32px;
    border-radius: 12px;
    text-align: center;
}

.error-card h1 {
    color: #dc2626;
    margin: 0 0 16px 0;
}

.error-card p {
    color: #7f1d1d;
}

.error-card a {
    color: #6366f1;
}
"""]


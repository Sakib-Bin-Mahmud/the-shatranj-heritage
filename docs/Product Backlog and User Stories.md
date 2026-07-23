# Product Backlog & User Stories

**Document Version:** 1.0  
**Document Status:** Draft  
**Product Name:** The Shatranj Heritage  
**Product Type:** Niche E-commerce Platform for Chess Merchandise  
**Prepared By:** Product Management, Business Analysis & Solution Architecture  
**Document Owner:** Product Management Team  
**Last Updated:** July 2026

# Section 1: Foundation

---

# **1. Document Purpose**

This document serves as the **master Product Backlog** for The Shatranj Heritage.

It translates the Product Vision, Business Requirements Document (BRD), and Software Requirements Specification (SRS) into actionable work items that can be implemented by engineering teams using Agile methodologies.

The backlog is intended to:

* Organize all product requirements into manageable Epics and User Stories.  
* Provide clear implementation priorities.  
* Maintain traceability from business goals to software features.  
* Define acceptance criteria for every feature.  
* Support sprint planning and release management.  
* Act as the primary reference for Product Managers, Developers, Designers, QA Engineers, and Scrum Masters.

This document is designed to evolve over time as the product grows.

---

# **2. Scope**

The backlog covers the implementation of **The Shatranj Heritage Version 1 (MVP)** and defines future enhancements planned for subsequent releases.

It includes:

* Customer-facing features  
* Administrative features  
* Commerce workflows  
* Payment and shipping  
* Inventory management  
* CMS  
* Reporting  
* Notifications  
* Marketplace preparation  
* Future ecosystem capabilities

---

# **3. Objectives**

The Product Backlog aims to ensure that development remains aligned with the business vision of creating Bangladesh's first dedicated chess e-commerce platform.

The objectives are to:

* Deliver the MVP efficiently.  
* Prioritize high-value features.  
* Maintain a customer-centric development approach.  
* Support iterative delivery.  
* Enable transparent planning and progress tracking.  
* Reduce ambiguity during implementation.

---

# **4. Audience**

This document is intended for:

| Stakeholder | Purpose |
| ----- | ----- |
| Product Manager | Feature prioritization and roadmap planning |
| Business Analyst | Requirement traceability and clarification |
| Solution Architect | Architecture validation |
| UI/UX Designer | User flow and interface design |
| Software Engineer | Feature implementation |
| QA Engineer | Test case creation and acceptance validation |
| Scrum Master | Sprint planning and backlog management |
| Project Manager | Release planning and progress tracking |
| Business Stakeholders | Scope validation and decision-making |

---

# **5. Agile Methodology**

The backlog follows Agile principles.

Development should be performed iteratively using short development cycles (sprints).

Each sprint should deliver potentially releasable increments of software.

Every User Story must satisfy the **Definition of Ready** before entering a sprint and the **Definition of Done** before being marked complete.

---

# **6. Story Writing Standard**

Every User Story in this document follows the standard format:

> **As a , I want , so that .**

Each story includes:

* Story ID  
* Epic  
* Priority  
* Description  
* Acceptance Criteria  
* Business Rules  
* Dependencies  
* Related Functional Requirements  
* Release Version

---

# **7. Story Identification Standard**

Stories use the following naming convention:

US-\<MODULE\>-\#\#\#

Examples:

US-AUTH-001  
US-CAT-014  
US-ORD-009  
US-PAY-005

Epic identifiers:

EP-01  
EP-02  
EP-03

Feature identifiers:

FT-AUTH-001  
FT-CAT-003

Requirement references point back to the SRS:

FR-AUTH-001  
FR-CAT-008  
FR-ORD-005

This convention ensures end-to-end traceability.

---

# **8. Story Lifecycle**

Every User Story progresses through the following workflow:

Draft  
   ↓  
Ready for Refinement  
   ↓  
Refined  
   ↓  
Ready for Sprint  
   ↓  
In Development  
   ↓  
Code Review  
   ↓  
Testing  
   ↓  
User Acceptance Testing  
   ↓  
Done

Stories may return to earlier stages if changes or defects are identified.

---

# **9. Priority Model (MoSCoW)**

The backlog uses the **MoSCoW prioritization framework**.

## **Must Have**

Critical functionality required for the MVP.

Without these stories, the product cannot be released.

Examples:

* Registration  
* Login  
* Shopping Cart  
* Checkout  
* Orders

---

## **Should Have**

Important functionality that significantly improves the user experience but is not essential for launch.

Examples:

* Wishlist  
* Reviews  
* Coupons  
* Buying Guides

---

## **Could Have**

Enhancements that add value but may be postponed without affecting the core business.

Examples:

* Product comparison  
* AI recommendations  
* Referral program

---

## **Won't Have (Current Release)**

Features intentionally deferred.

Examples:

* Marketplace  
* Native Mobile Apps  
* International Shipping  
* Equipment Rental

---

# **10. Story Estimation**

Story estimation should use **Story Points** based on relative complexity.

| Story Points | Complexity |
| ----- | ----- |
| 1 | Very Small |
| 2 | Small |
| 3 | Medium |
| 5 | Moderate |
| 8 | Large |
| 13 | Very Large |
| 21 | Epic / Requires Breakdown |

Stories estimated above **13 points** should be reviewed and split into smaller stories before implementation.

---

# **11. Definition of Ready (DoR)**

A User Story is considered **Ready** when:

* The business objective is clearly understood.  
* The story follows the standard user story format.  
* Acceptance criteria are complete and testable.  
* Dependencies are identified.  
* UX considerations have been clarified where necessary.  
* Open questions have been resolved or documented.  
* The Product Owner has approved the story for implementation.  
* The development team understands the expected outcome.

Stories that do not meet these criteria should not be selected for a sprint.

---

# **12. Definition of Done (DoD)**

A User Story is considered **Done** only when:

* The functionality has been implemented.  
* Code has been peer-reviewed.  
* Unit tests have been written and passed.  
* Integration tests have passed.  
* Acceptance criteria have been satisfied.  
* No critical or high-severity defects remain.  
* Relevant documentation has been updated.  
* The Product Owner has accepted the implementation.  
* The feature has been deployed to the target environment for the current release stage (e.g., staging or production, as applicable).

---

# **13. Epic Overview**

The Shatranj Heritage Product Backlog is organized into the following epics.

| Epic ID | Epic | Priority | Release |
| ----- | ----- | ----- | ----- |
| EP-01 | Authentication & Authorization | Must | MVP |
| EP-02 | Customer Management | Must | MVP |
| EP-03 | Product Catalog | Must | MVP |
| EP-04 | Search & Discovery | Must | MVP |
| EP-05 | Shopping Cart | Must | MVP |
| EP-06 | Wishlist | Should | V2 |
| EP-07 | Checkout | Must | MVP |
| EP-08 | Payment Management | Must | MVP |
| EP-09 | Order Management | Must | MVP |
| EP-10 | Shipping & Fulfillment | Must | MVP |
| EP-11 | Reviews & Ratings | Should | V2 |
| EP-12 | Notifications | Must | MVP |
| EP-13 | Administration | Must | MVP |
| EP-14 | Inventory Management | Must | MVP |
| EP-15 | Promotions & Discounts | Should | V2 |
| EP-16 | Content Management System (CMS) | Should | V2 |
| EP-17 | Reporting & Analytics | Must | MVP |
| EP-18 | Vendor Marketplace | Won't | V3 |

> **Note:** Some "Should" features (e.g., a basic coupon engine or limited CMS capabilities) may be selectively included in the MVP if they are essential for launch, while more advanced functionality remains scheduled for V2.

---

# **14. MVP Feature Summary**

The MVP is designed to validate the business hypothesis that there is sufficient demand for a dedicated chess e-commerce platform in Bangladesh.

The MVP includes:

### **Customer Experience**

* Registration & Login  
* Guest Checkout  
* Product Browsing  
* Product Search  
* Product Details  
* Shopping Cart  
* Checkout  
* Order Tracking  
* Customer Profile

---

### **Commerce**

* Product Catalog  
* Categories  
* Inventory  
* Payments  
* Shipping  
* Order Management

---

### **Administration**

* Product Management  
* Inventory Management  
* Customer Management  
* Order Management  
* Reports  
* User Management

---

### **Platform**

* Notifications  
* Security  
* Audit Logging  
* Monitoring  
* CMS (Basic)

---

# **15. Release Strategy**

The product roadmap is divided into three major releases.

| Release | Objective |
| ----- | ----- |
| MVP (V1) | Launch Bangladesh's first dedicated chess e-commerce platform with core shopping, payment, inventory, and administration capabilities. |
| V2 | Enhance customer engagement through content, loyalty, promotions, reviews, wishlists, and richer commerce features. |
| V3 | Transform The Shatranj Heritage into a broader chess ecosystem with a multi-vendor marketplace, mobile applications, regional expansion, and AI-assisted experiences. |

---

# **16. Traceability Structure**

Every User Story must trace back to a business requirement and software requirement.

Product Vision  
        ↓  
Business Requirement (BRD)  
        ↓  
Software Requirement (SRS)  
        ↓  
Epic  
        ↓  
Feature  
        ↓  
User Story  
        ↓  
Acceptance Criteria  
        ↓  
Test Cases

This structure ensures complete visibility from strategic goals to implementation and verification.

---

# **17. Backlog Governance**

To keep the backlog healthy and actionable:

* **Product Owner:** Owns prioritization and approves scope changes.  
* **Business Analyst:** Refines requirements and maintains traceability.  
* **Engineering Team:** Estimates effort, identifies technical dependencies, and proposes implementation approaches.  
* **QA Team:** Reviews acceptance criteria for testability and prepares validation scenarios.  
* **Scrum Master / Project Manager:** Facilitates backlog refinement and sprint planning.

Backlog refinement should be conducted regularly to split large stories, clarify acceptance criteria, reprioritize work, and remove obsolete items.

---

# **18. Section Summary**

Section 1 establishes the standards, governance, and structure for the The Shatranj Heritage Product Backlog. It defines how user stories are written, prioritized, estimated, tracked, and traced to higher-level requirements.

The following sections will contain the implementation-ready backlog itself, beginning with **EP-01: Authentication & Authorization**, followed by the remaining epics in priority order.

# Epic Board

# **EP-01: Authentication & Authorization**

## **Epic Overview**

**Epic ID:** EP-01  
**Priority:** Must Have (MVP)

### **Goal**

Enable customers and administrators to securely access the platform while protecting customer data and business operations.

---

## **Features**

| Feature ID | Feature | MVP |
| ----- | ----- | ----- |
| FT-AUTH-001 | Customer Registration | ✓ |
| FT-AUTH-002 | Customer Login | ✓ |
| FT-AUTH-003 | Guest Checkout | ✓ |
| FT-AUTH-004 | Forgot Password | ✓ |
| FT-AUTH-005 | Password Reset | ✓ |
| FT-AUTH-006 | Logout | ✓ |
| FT-AUTH-007 | Session Management | ✓ |
| FT-AUTH-008 | Email Verification | Should |
| FT-AUTH-009 | Mobile OTP Verification | Should |
| FT-AUTH-010 | Social Login | Won't (MVP) |

---

## **US-AUTH-001 — Register with Email**

**Priority:** Must

**Story**

> As a guest, I want to register using my email address so that I can create an account and purchase products.

**Acceptance Criteria**

* Registration page is publicly accessible.  
* Email address is mandatory and unique.  
* Required fields are validated.  
* Password meets the security policy.  
* Customer account is created successfully.  
* Customer is redirected to their account after successful registration.

**Business Rules**

* Email addresses must be unique.  
* Passwords are stored using secure hashing.  
* Duplicate registrations are rejected.

**Dependencies**

* Customer Module  
* Notification Service

**Related SRS**

* FR-AUTH-001

**Release**

* MVP

---

## **US-AUTH-002 — Register with Mobile Number**

**Priority:** Must

**Story**

> As a guest, I want to register using my mobile number so that I can create an account even if I do not frequently use email.

**Acceptance Criteria**

* Mobile number follows the supported Bangladeshi format.  
* Duplicate mobile numbers are rejected.  
* Account is created after successful validation.

**Business Rules**

* One account per verified mobile number.  
* Mobile number becomes part of the customer's primary contact information.

**Related SRS**

* FR-AUTH-002

---

## **US-AUTH-003 — Login**

**Priority:** Must

**Story**

> As a registered customer, I want to log in securely so that I can access my account and purchase history.

**Acceptance Criteria**

* Login with email or mobile number.  
* Correct password grants access.  
* Incorrect credentials display a generic error message.  
* Successful login redirects to the previous page or account dashboard.

**Business Rules**

* Failed login attempts are rate-limited.  
* Sessions expire after a configurable period of inactivity.

**Related SRS**

* FR-AUTH-003

---

## **US-AUTH-004 — Guest Checkout**

**Priority:** Must

**Story**

> As a guest, I want to purchase products without creating an account so that I can complete my order quickly.

**Acceptance Criteria**

* Guest users can add products to the cart.  
* Checkout is available without registration.  
* Shipping and billing details are collected during checkout.  
* Order confirmation is sent via email or SMS.

**Business Rules**

* Guest orders are linked to the provided contact information.  
* Guests may optionally create an account after purchase.

**Related SRS**

* FR-CHK-001

---

## **US-AUTH-005 — Forgot Password**

**Priority:** Must

**Story**

> As a customer, I want to request a password reset so that I can regain access if I forget my password.

**Acceptance Criteria**

* Password reset request can be initiated from the login page.  
* Reset link or OTP is sent to the registered email or mobile number.  
* Invalid or expired reset requests are rejected.

**Related SRS**

* FR-AUTH-005

---

## **US-AUTH-006 — Reset Password**

**Priority:** Must

**Story**

> As a customer, I want to set a new password using a secure reset process so that I can regain access to my account.

**Acceptance Criteria**

* Reset token or OTP is validated.  
* New password complies with password policy.  
* Existing sessions are invalidated after a successful reset.  
* User is notified that the password has been changed.

**Related SRS**

* FR-AUTH-006

---

## **US-AUTH-007 — Logout**

**Priority:** Must

**Story**

> As a logged-in user, I want to log out securely so that my account remains protected on shared devices.

**Acceptance Criteria**

* Session tokens are invalidated.  
* User is redirected to the home page or login page.  
* Protected pages cannot be accessed after logout without re-authentication.

**Related SRS**

* FR-AUTH-007

---

## **US-AUTH-008 — Email Verification**

**Priority:** Should

**Story**

> As a customer, I want to verify my email address so that my account is trusted and I can receive order-related communications.

**Acceptance Criteria**

* Verification email is sent after registration.  
* Verification link expires after a configurable time.  
* User can request a new verification email if the previous one expires.

**Release**

* V2

---

## **US-AUTH-009 — Mobile OTP Verification**

**Priority:** Should

**Story**

> As a customer, I want to verify my mobile number using an OTP so that my contact information is confirmed.

**Acceptance Criteria**

* OTP is sent to the registered mobile number.  
* OTP expires after a configurable time.  
* Incorrect or expired OTPs are rejected.  
* Users may request a limited number of OTP resends.

**Release**

* V2

---

## **US-AUTH-010 — Social Login**

**Priority:** Won't (MVP)

**Story**

> As a customer, I want to sign in using my Google or Facebook account so that I can access the platform quickly.

**Acceptance Criteria**

* Google OAuth integration.  
* Facebook Login integration.  
* Existing accounts can be linked to social identities.

**Release**

* V3

---

# **EP-02: Customer Management**

## **Epic Overview**

**Epic ID:** EP-02  
**Priority:** Must Have (MVP)

### **Goal**

Enable customers to manage their personal information, addresses, and account preferences, while providing administrators with essential customer management capabilities.

---

## **Features**

| Feature ID | Feature | MVP |
| ----- | ----- | ----- |
| FT-CUS-001 | Customer Profile | ✓ |
| FT-CUS-002 | Address Management | ✓ |
| FT-CUS-003 | Order History | ✓ |
| FT-CUS-004 | Account Settings | ✓ |
| FT-CUS-005 | Communication Preferences | Should |
| FT-CUS-006 | Account Deactivation | Should |

---

## **US-CUS-001 — View Profile**

**Priority:** Must

**Story**

> As a customer, I want to view my profile information so that I can verify and manage my personal details.

**Acceptance Criteria**

* Profile displays name, email, mobile number, and account details.  
* Information reflects the latest saved data.  
* Only authenticated users can access their own profile.

**Related SRS**

* FR-CUS-001

---

## **US-CUS-002 — Update Profile**

**Priority:** Must

**Story**

> As a customer, I want to update my profile information so that my account remains accurate.

**Acceptance Criteria**

* Customer can update editable profile fields.  
* Required validations are applied.  
* Successful updates are reflected immediately.  
* Audit information is recorded for profile changes.

**Related SRS**

* FR-CUS-002

---

## **US-CUS-003 — Manage Addresses**

**Priority:** Must

**Story**

> As a customer, I want to manage multiple delivery addresses so that I can ship orders to different locations.

**Acceptance Criteria**

* Customers can add, edit, and delete addresses.  
* One address can be marked as the default.  
* Address validation is performed before saving.  
* Addresses are available during checkout.

**Related SRS**

* FR-CUS-003

---

## **US-CUS-004 — View Order History**

**Priority:** Must

**Story**

> As a customer, I want to view my previous orders so that I can track purchases and reorder products if needed.

**Acceptance Criteria**

* Orders are listed in reverse chronological order.  
* Each order shows its status, total amount, and date.  
* Customers can access order details from the list.

**Related SRS**

* FR-ORD-004

---

## **US-CUS-005 — Update Account Settings**

**Priority:** Must

**Story**

> As a customer, I want to manage my account settings so that I can personalize my experience.

**Acceptance Criteria**

* Customers can update preferences such as language and notification settings.  
* Changes are saved successfully.  
* Preferences are applied to future interactions where applicable.

**Related SRS**

* FR-CUS-005

---

## **US-CUS-006 — Manage Communication Preferences**

**Priority:** Should

**Story**

> As a customer, I want to control marketing communications so that I receive only the notifications I choose.

**Acceptance Criteria**

* Customers can opt in or out of promotional emails and SMS.  
* Transactional notifications remain enabled.  
* Preference changes take effect for future campaigns.

**Release**

* V2

---

## **US-CUS-007 — Deactivate Account**

**Priority:** Should

**Story**

> As a customer, I want to deactivate my account so that I can stop using the platform while preserving my order history.

**Acceptance Criteria**

* Customers can request account deactivation.  
* Active orders prevent immediate deactivation until fulfillment is complete.  
* Account data is retained according to legal and business retention policies.  
* Customers receive confirmation of the deactivation request.

**Release**

* V2

# **EP-03: Product Catalog**

## **Epic Overview**

**Epic ID:** EP-03  
**Priority:** Must Have (MVP)

### **Goal**

Provide customers with a rich, intuitive, and informative product browsing experience that showcases chess merchandise while helping them make informed purchasing decisions.

---

## **Features**

| Feature ID | Feature | MVP |
| ----- | ----- | ----- |
| FT-CAT-001 | Product Listing | ✓ |
| FT-CAT-002 | Product Details | ✓ |
| FT-CAT-003 | Product Categories | ✓ |
| FT-CAT-004 | Product Images | ✓ |
| FT-CAT-005 | Product Variants | ✓ |
| FT-CAT-006 | Related Products | ✓ |
| FT-CAT-007 | Featured Products | ✓ |
| FT-CAT-008 | Product Availability | ✓ |
| FT-CAT-009 | Recently Viewed Products | Should |
| FT-CAT-010 | Product Comparison | Could |

---

## **US-CAT-001 — Browse Products**

**Priority:** Must

**Story**

> As a customer, I want to browse all available products so that I can discover chess merchandise that interests me.

### **Acceptance Criteria**

* Products are displayed in a responsive grid or list layout.  
* Pagination or infinite scrolling is supported.  
* Each product card displays:  
  * Image  
  * Name  
  * Price  
  * Stock status  
* Clicking a product opens the product details page.

**Related SRS**

* FR-CAT-001

---

## **US-CAT-002 — View Product Details**

**Priority:** Must

**Story**

> As a customer, I want to view detailed product information so that I can decide whether to purchase it.

### **Acceptance Criteria**

Product page displays:

* Product name  
* Description  
* High-quality images  
* Price  
* Material  
* Dimensions  
* Weight  
* Category  
* SKU  
* Stock availability  
* Delivery estimate  
* Customer reviews (if available)

---

## **US-CAT-003 — Browse by Category**

**Priority:** Must

**Story**

> As a customer, I want to browse products by category so that I can quickly find the type of chess product I'm looking for.

### **Acceptance Criteria**

Categories include, but are not limited to:

* Chess Sets  
* Chess Boards  
* Chess Pieces  
* Tournament Equipment  
* Chess Clocks  
* Chess Books  
* Accessories  
* Customized Products

Customers can navigate between categories without losing applied filters where appropriate.

---

## **US-CAT-004 — View Product Images**

**Priority:** Must

**Story**

> As a customer, I want to view multiple images of a product so that I can inspect it before purchasing.

### **Acceptance Criteria**

* Multiple product images are supported.  
* Thumbnail gallery is displayed.  
* Images can be enlarged.  
* Zoom functionality is available on desktop.  
* Images are optimized for fast loading.

---

## **US-CAT-005 — Select Product Variant**

**Priority:** Must

**Story**

> As a customer, I want to choose product variants such as size or material so that I receive the exact product I want.

### **Acceptance Criteria**

Supported variants may include:

* Board size  
* Wood type  
* Finish  
* Piece style  
* Personalized engraving

Unavailable variants cannot be selected.

---

## **US-CAT-006 — View Related Products**

**Priority:** Must

**Story**

> As a customer, I want to see related products so that I can discover complementary items.

### **Acceptance Criteria**

Examples:

* Matching chess clocks  
* Chess bags  
* Extra queens  
* Scorebooks  
* Books

Related products should belong to similar categories or purchasing patterns.

---

## **US-CAT-007 — View Featured Products**

**Priority:** Must

**Story**

> As a visitor, I want to see featured products on the homepage so that I can discover popular or promoted items.

### **Acceptance Criteria**

Homepage supports:

* Featured products  
* New arrivals  
* Best sellers  
* Editor's Picks

---

## **US-CAT-008 — View Stock Availability**

**Priority:** Must

**Story**

> As a customer, I want to know whether a product is available so that I avoid ordering out-of-stock items.

### **Acceptance Criteria**

Display:

* In Stock  
* Low Stock  
* Out of Stock

Out-of-stock products cannot be added to the cart.

---

## **US-CAT-009 — Recently Viewed Products**

**Priority:** Should

**Release:** V2

---

## **US-CAT-010 — Compare Products**

**Priority:** Could

**Release:** V3

---

# **EP-04: Search & Discovery**

## **Epic Overview**

**Epic ID:** EP-04

### **Goal**

Help customers find products quickly using powerful search and filtering capabilities.

---

## **Features**

| Feature | MVP |
| ----- | ----- |
| Keyword Search | ✓ |
| Category Filter | ✓ |
| Price Filter | ✓ |
| Material Filter | ✓ |
| Sorting | ✓ |
| Search Suggestions | Should |
| AI Search | Could |

---

## **US-SRC-001 — Search Products**

**Priority:** Must

**Story**

> As a customer, I want to search for products using keywords so that I can quickly locate specific items.

### **Acceptance Criteria**

Search by:

* Product name  
* SKU  
* Category  
* Description

Search results should appear within one second under expected load.

---

## **US-SRC-002 — Filter Products**

**Priority:** Must

**Story**

> As a customer, I want to filter products so that I only see relevant items.

### **Acceptance Criteria**

Supported filters:

* Price range  
* Category  
* Material  
* Brand  
* Availability

Multiple filters can be applied simultaneously.

---

## **US-SRC-003 — Sort Products**

**Priority:** Must

**Story**

> As a customer, I want to sort products so that I can browse them according to my preferences.

### **Acceptance Criteria**

Sorting options include:

* Price (Low → High)  
* Price (High → Low)  
* Newest  
* Best Selling  
* Highest Rated  
* Alphabetical

---

## **US-SRC-004 — Search Suggestions**

**Priority:** Should

**Release:** V2

Autocomplete suggestions appear while typing.

---

## **US-SRC-005 — No Search Results**

**Priority:** Must

**Story**

> As a customer, I want helpful feedback when no products match my search so that I can continue browsing effectively.

### **Acceptance Criteria**

System displays:

* No results message  
* Suggested categories  
* Featured products  
* Search tips

---

## **US-SRC-006 — Recently Searched Terms**

**Priority:** Should

**Release:** V2

---

## **US-SRC-007 — AI Product Search**

**Priority:** Could

**Release:** V3

---

# **EP-05: Shopping Cart**

## **Epic Overview**

**Epic ID:** EP-05

**Priority:** Must

### **Goal**

Allow customers to prepare purchases before checkout while maintaining an accurate representation of product availability and pricing.

---

## **Features**

| Feature | MVP |
| ----- | ----- |
| Add to Cart | ✓ |
| Update Quantity | ✓ |
| Remove Item | ✓ |
| View Cart | ✓ |
| Cart Summary | ✓ |
| Save Cart | Should |
| Persistent Cart | Should |

---

## **US-CRT-001 — Add Product to Cart**

**Priority:** Must

**Story**

> As a customer, I want to add products to my shopping cart so that I can purchase multiple items together.

### **Acceptance Criteria**

* Available products can be added.  
* Selected variant is stored.  
* Quantity defaults to one.  
* Cart updates immediately.  
* Cart icon reflects the updated item count.

---

## **US-CRT-002 — Update Quantity**

**Priority:** Must

**Story**

> As a customer, I want to modify item quantities so that I can purchase the desired number of products.

### **Acceptance Criteria**

* Increase quantity.  
* Decrease quantity.  
* Quantity cannot exceed available inventory.  
* Total price updates automatically.

---

## **US-CRT-003 — Remove Product**

**Priority:** Must

**Story**

> As a customer, I want to remove products from my cart so that I can update my purchase before checkout.

### **Acceptance Criteria**

* Remove individual products.  
* Confirmation is shown when appropriate.  
* Cart totals are recalculated immediately.

---

## **US-CRT-004 — View Shopping Cart**

**Priority:** Must

**Story**

> As a customer, I want to review my shopping cart so that I can verify my order before checkout.

### **Acceptance Criteria**

Display:

* Product image  
* Product name  
* Variant  
* Quantity  
* Unit price  
* Subtotal  
* Estimated total  
* Continue Shopping button  
* Proceed to Checkout button

---

## **US-CRT-005 — View Cart Summary**

**Priority:** Must

**Story**

> As a customer, I want to see a clear order summary so that I understand the cost before checkout.

### **Acceptance Criteria**

Display:

* Item subtotal  
* Estimated shipping  
* Estimated tax (if applicable)  
* Discount amount  
* Grand total

---

## **US-CRT-006 — Empty Cart**

**Priority:** Must

**Story**

> As a customer, I want to receive helpful guidance when my cart is empty so that I can easily continue shopping.

### **Acceptance Criteria**

Display:

* Empty cart illustration  
* "Your cart is empty" message  
* Continue Shopping button  
* Recommended products

---

## **US-CRT-007 — Save Cart**

**Priority:** Should

**Release:** V2

Customers can intentionally save their cart for future purchases.

---

## **US-CRT-008 — Persistent Cart**

**Priority:** Should

**Release:** V2

Authenticated customers retain their cart across devices and sessions.

---

## **US-CRT-009 — Inventory Validation**

**Priority:** Must

**Story**

> As a customer, I want the cart to reflect current inventory so that I cannot proceed with unavailable quantities.

### **Acceptance Criteria**

* Inventory is validated when items are added.  
* Inventory is revalidated before checkout.  
* Customers are informed if quantities must be adjusted due to stock changes.

---

## **US-CRT-010 — Cart Expiration**

**Priority:** Could

**Release:** V3

Customers are notified when items have remained in the cart for an extended period or become unavailable.

# **EP-06: Wishlist**

## **Epic Overview**

**Epic ID:** EP-06  
**Priority:** Should Have (V2)

### **Goal**

Allow customers to save products for future purchase and improve customer retention.

---

## **Features**

| Feature ID | Feature | Release |
| ----- | ----- | ----- |
| FT-WSH-001 | Add to Wishlist | V2 |
| FT-WSH-002 | View Wishlist | V2 |
| FT-WSH-003 | Remove from Wishlist | V2 |
| FT-WSH-004 | Move to Cart | V2 |
| FT-WSH-005 | Wishlist Availability Updates | V3 |

---

## **US-WSH-001 — Add Product to Wishlist**

**Priority:** Should

**Story**

> As a customer, I want to save products to my wishlist so that I can purchase them later.

### **Acceptance Criteria**

* Authenticated customers can add products to a wishlist.  
* Duplicate wishlist entries are prevented.  
* The wishlist icon reflects the saved status.

---

## **US-WSH-002 — View Wishlist**

**Priority:** Should

**Story**

> As a customer, I want to view my wishlist so that I can review products I intend to purchase.

### **Acceptance Criteria**

* Wishlist displays saved products with image, name, price, and stock status.  
* Customers can navigate directly to the product page.

---

## **US-WSH-003 — Remove Product from Wishlist**

**Priority:** Should

**Story**

> As a customer, I want to remove products from my wishlist so that it stays relevant.

### **Acceptance Criteria**

* Products can be removed individually.  
* The wishlist count updates immediately.

---

## **US-WSH-004 — Move Wishlist Item to Cart**

**Priority:** Should

**Story**

> As a customer, I want to move wishlist items to my shopping cart so that I can purchase them easily.

### **Acceptance Criteria**

* Selected product is added to the cart.  
* Product is removed from the wishlist if the customer chooses.  
* Inventory is validated before adding to the cart.

---

# **EP-07: Checkout**

## **Epic Overview**

**Epic ID:** EP-07  
**Priority:** Must Have (MVP)

### **Goal**

Provide a simple, secure, and frictionless checkout experience.

---

## **Features**

| Feature ID | Feature | MVP |
| ----- | ----- | ----- |
| FT-CHK-001 | Checkout Workflow | ✓ |
| FT-CHK-002 | Address Selection | ✓ |
| FT-CHK-003 | Shipping Method | ✓ |
| FT-CHK-004 | Order Summary | ✓ |
| FT-CHK-005 | Coupon Application | V2 |
| FT-CHK-006 | Guest Checkout | ✓ |

---

## **US-CHK-001 — Start Checkout**

**Priority:** Must

**Story**

> As a customer, I want to begin the checkout process so that I can purchase the items in my cart.

### **Acceptance Criteria**

* Checkout is accessible from the cart.  
* Empty carts cannot proceed to checkout.  
* Inventory is validated before continuing.

---

## **US-CHK-002 — Select Shipping Address**

**Priority:** Must

**Story**

> As a customer, I want to choose or add a shipping address so that my order is delivered correctly.

### **Acceptance Criteria**

* Existing addresses can be selected.  
* New addresses can be created during checkout.  
* Address validation is performed before order placement.

---

## **US-CHK-003 — Select Shipping Method**

**Priority:** Must

**Story**

> As a customer, I want to choose a shipping option so that I can balance delivery speed and cost.

### **Acceptance Criteria**

* Available shipping methods are displayed with estimated delivery times and costs.  
* Selection updates the order summary.

---

## **US-CHK-004 — Review Order**

**Priority:** Must

**Story**

> As a customer, I want to review my order before payment so that I can verify all details.

### **Acceptance Criteria**

The review page displays:

* Items  
* Quantities  
* Prices  
* Shipping cost  
* Discounts  
* Total amount  
* Selected address  
* Selected shipping method

---

## **US-CHK-005 — Apply Coupon**

**Priority:** Should

**Story**

> As a customer, I want to apply a valid coupon so that I can receive eligible discounts.

### **Acceptance Criteria**

* Coupon codes are validated.  
* Invalid or expired coupons display a meaningful error.  
* Discounts are reflected immediately in the order summary.

**Release:** V2

---

## **US-CHK-006 — Place Order**

**Priority:** Must

**Story**

> As a customer, I want to place my order successfully so that my purchase can be processed.

### **Acceptance Criteria**

* Payment is initiated (or COD selected).  
* Inventory is reserved or deducted according to business rules.  
* A unique order number is generated.  
* Confirmation page is displayed.  
* Confirmation email/SMS is sent.

---

# **EP-08: Payment Management**

## **Epic Overview**

**Epic ID:** EP-08  
**Priority:** Must Have (MVP)

### **Goal**

Support secure and reliable payment processing through locally relevant payment methods.

---

## **Features**

| Feature | MVP |
| ----- | ----- |
| SSLCommerz Integration | ✓ |
| bKash | ✓ |
| Nagad | ✓ |
| Rocket | ✓ |
| Visa / Mastercard | ✓ |
| Cash on Delivery | ✓ |
| Refund Management | V2 |

---

## **US-PAY-001 — Pay Online**

**Priority:** Must

**Story**

> As a customer, I want to pay online using supported payment methods so that I can complete my purchase securely.

### **Acceptance Criteria**

* Customer can select a supported payment method.  
* Payment request is sent to the gateway.  
* Successful transactions update the order status.

---

## **US-PAY-002 — Cash on Delivery**

**Priority:** Must

**Story**

> As a customer, I want to choose Cash on Delivery so that I can pay when my order arrives.

### **Acceptance Criteria**

* COD availability is validated based on business rules.  
* Order is marked as "Awaiting Payment."  
* Customers receive COD instructions where applicable.

---

## **US-PAY-003 — Payment Failure Handling**

**Priority:** Must

**Story**

> As a customer, I want clear feedback when a payment fails so that I can retry or choose another payment method.

### **Acceptance Criteria**

* Failed payments do not create duplicate orders.  
* Clear error messages are displayed.  
* Customers can retry payment.

---

## **US-PAY-004 — View Payment Status**

**Priority:** Must

**Story**

> As a customer, I want to see the payment status of my order so that I know whether my purchase was successful.

### **Acceptance Criteria**

Statuses include:

* Pending  
* Successful  
* Failed  
* Refunded  
* Cancelled

---

## **US-PAY-005 — Refund Payment**

**Priority:** Should

**Story**

> As an administrator, I want to process eligible refunds so that customers receive their money when appropriate.

### **Acceptance Criteria**

* Refund requests are recorded.  
* Refund status is tracked.  
* Customer receives a refund notification.

**Release:** V2

---

# **EP-09: Order Management**

## **Epic Overview**

**Epic ID:** EP-09  
**Priority:** Must Have (MVP)

### **Goal**

Manage the complete order lifecycle from placement through fulfillment.

---

## **Features**

| Feature | MVP |
| ----- | ----- |
| Order Creation | ✓ |
| Order Tracking | ✓ |
| Order History | ✓ |
| Order Cancellation | ✓ |
| Order Status Updates | ✓ |
| Returns | V2 |

---

## **US-ORD-001 — Create Order**

**Priority:** Must

**Story**

> As a customer, I want my order to be created successfully after checkout so that the fulfillment process can begin.

### **Acceptance Criteria**

* Unique order number generated.  
* Order stored successfully.  
* Inventory updated according to business rules.

---

## **US-ORD-002 — Track Order**

**Priority:** Must

**Story**

> As a customer, I want to track my order so that I know its current progress.

### **Acceptance Criteria**

Statuses include:

* Pending  
* Confirmed  
* Processing  
* Packed  
* Shipped  
* Delivered  
* Cancelled

---

## **US-ORD-003 — Cancel Order**

**Priority:** Must

**Story**

> As a customer, I want to cancel an eligible order so that I can change my mind before shipment.

### **Acceptance Criteria**

* Cancellation is allowed only before shipment.  
* Inventory is restored when applicable.  
* Payment refund workflow is triggered if necessary.

---

## **US-ORD-004 — View Order Details**

**Priority:** Must

**Story**

> As a customer, I want to view detailed information about my order so that I can verify what I purchased.

### **Acceptance Criteria**

Display:

* Items  
* Prices  
* Shipping address  
* Payment method  
* Order timeline  
* Tracking information (if available)

---

# **EP-10: Shipping & Fulfillment**

## **Epic Overview**

**Epic ID:** EP-10  
**Priority:** Must Have (MVP)

### **Goal**

Ensure reliable shipment processing and delivery visibility.

---

## **Features**

| Feature | MVP |
| ----- | ----- |
| Shipping Calculation | ✓ |
| Courier Integration | ✓ |
| Tracking Number | ✓ |
| Delivery Status | ✓ |
| Multiple Couriers | ✓ |

---

## **US-SHP-001 — Calculate Shipping**

**Priority:** Must

**Story**

> As a customer, I want shipping charges to be calculated automatically so that I know the total cost before payment.

### **Acceptance Criteria**

* Shipping cost is calculated based on configurable business rules.  
* Cost is displayed before payment.  
* Changes in address update the shipping estimate.

---

## **US-SHP-002 — Assign Courier**

**Priority:** Must

**Story**

> As an order manager, I want to assign a courier to an order so that it can be dispatched efficiently.

### **Acceptance Criteria**

* Eligible courier providers can be selected.  
* Shipment record is created.  
* Tracking number can be recorded.

---

## **US-SHP-003 — Track Shipment**

**Priority:** Must

**Story**

> As a customer, I want to view shipment tracking information so that I know when my order will arrive.

### **Acceptance Criteria**

* Tracking number is displayed once available.  
* Shipment status is updated.  
* Estimated delivery date is shown when provided by the courier.

---

## **US-SHP-004 — Delivery Confirmation**

**Priority:** Must

**Story**

> As a customer, I want to receive confirmation when my order is delivered so that I know the order has been completed.

### **Acceptance Criteria**

* Delivery status is updated to "Delivered."  
* Customer receives an email and/or SMS notification.  
* Order timeline reflects the delivery event.

# **EP-11: Reviews & Ratings**

## **Epic Overview**

**Epic ID:** EP-11  
**Priority:** Should Have (V2)

### **Goal**

Enable customers to share feedback on purchased products, helping future buyers make informed decisions while providing valuable insights to the business.

## **Features**

| Feature ID | Feature | Release |
| ----- | ----- | ----- |
| FT-REV-001 | Product Rating | V2 |
| FT-REV-002 | Product Review | V2 |
| FT-REV-003 | Review Moderation | V2 |
| FT-REV-004 | Review Reporting | V3 |

### **Key User Stories**

## **US-REV-001 — Rate a Product**

**Priority:** Should

> As a customer, I want to rate a purchased product so that I can share my experience.

**Acceptance Criteria**

* Only verified purchasers can submit ratings.  
* Rating scale is 1–5 stars.  
* Average rating updates after approval.

---

## **US-REV-002 — Write a Review**

**Priority:** Should

> As a customer, I want to write a review so that I can help other buyers.

**Acceptance Criteria**

* Text review is supported.  
* Review is linked to a verified purchase.  
* Reviews may require moderation before publication.

---

# **EP-12: Notifications**

## **Epic Overview**

**Epic ID:** EP-12  
**Priority:** Must Have (MVP)

### **Goal**

Keep customers informed throughout their shopping journey.

## **Features**

* Account notifications  
* Order confirmations  
* Payment confirmations  
* Shipping updates  
* Delivery notifications  
* Password reset notifications  
* Promotional campaigns (V2)

### **Key User Stories**

## **US-NOT-001 — Order Confirmation**

**Priority:** Must

> As a customer, I want to receive an order confirmation so that I know my order was placed successfully.

**Acceptance Criteria**

* Confirmation is sent via email.  
* SMS is sent if a mobile number is available.  
* Includes order number and summary.

---

## **US-NOT-002 — Shipping Notification**

**Priority:** Must

> As a customer, I want to receive shipping updates so that I know when to expect delivery.

**Acceptance Criteria**

* Notification sent when order is dispatched.  
* Tracking number included when available.

---

# **EP-13: Administration**

## **Epic Overview**

**Epic ID:** EP-13  
**Priority:** Must Have (MVP)

### **Goal**

Provide administrators with complete operational control over the platform.

## **Features**

* Dashboard  
* User Management  
* Product Management  
* Category Management  
* Order Management  
* Customer Management  
* Role Management  
* Audit Logs  
* System Settings

### **Key User Stories**

## **US-ADM-001 — Manage Products**

**Priority:** Must

> As an administrator, I want to create, edit, and archive products so that the catalog remains accurate.

**Acceptance Criteria**

* CRUD operations for products.  
* Product visibility can be controlled.  
* Changes are logged.

---

## **US-ADM-002 — Manage Categories**

**Priority:** Must

> As an administrator, I want to organize products into categories so that customers can browse efficiently.

---

## **US-ADM-003 — Manage Users**

**Priority:** Must

> As an administrator, I want to manage customer accounts so that I can resolve account-related issues.

---

## **US-ADM-004 — Assign Roles**

**Priority:** Must

> As a Super Admin, I want to assign roles and permissions so that staff members only access authorized features.

---

# **EP-14: Inventory Management**

## **Epic Overview**

**Epic ID:** EP-14  
**Priority:** Must Have (MVP)

### **Goal**

Maintain accurate stock levels and prevent overselling.

## **Features**

* Stock Management  
* Stock Adjustments  
* Low Stock Alerts  
* Inventory History  
* SKU Management  
* Warehouse Support (Future)

### **Key User Stories**

## **US-INV-001 — Update Inventory**

**Priority:** Must

> As an inventory manager, I want to adjust stock levels so that inventory remains accurate.

---

## **US-INV-002 — Low Stock Alerts**

**Priority:** Must

> As an inventory manager, I want to receive low stock alerts so that products can be replenished before they sell out.

---

## **US-INV-003 — Inventory History**

**Priority:** Must

> As an administrator, I want to view inventory changes so that stock movements are auditable.

---

# **EP-15: Promotions & Discounts**

## **Epic Overview**

**Epic ID:** EP-15  
**Priority:** Should Have (V2)

### **Goal**

Increase sales through promotional campaigns.

## **Features**

* Coupon Management  
* Percentage Discounts  
* Fixed Discounts  
* Seasonal Campaigns  
* Free Shipping Promotions

### **Key User Stories**

## **US-PRM-001 — Create Coupon**

> As a marketing manager, I want to create promotional coupons so that I can increase conversions.

---

## **US-PRM-002 — Schedule Promotions**

> As a marketing manager, I want promotions to activate automatically on specific dates so that campaigns run without manual intervention.

---

# **EP-16: Content Management System (CMS)**

## **Epic Overview**

**Epic ID:** EP-16  
**Priority:** Should Have (V2)

### **Goal**

Allow non-technical staff to manage website content.

## **Features**

* Homepage banners  
* Landing pages  
* Blog management  
* Buying guides  
* FAQ  
* Static pages

### **Key User Stories**

## **US-CMS-001 — Publish Blog**

> As a content manager, I want to publish chess-related articles so that I can educate and engage customers.

---

## **US-CMS-002 — Manage Homepage**

> As a content manager, I want to update homepage banners so that seasonal campaigns are highlighted.

---

# **EP-17: Reporting & Analytics**

## **Epic Overview**

**Epic ID:** EP-17  
**Priority:** Must Have (MVP)

### **Goal**

Provide actionable insights for business and operational decision-making.

## **Features**

* Sales Reports  
* Product Performance  
* Inventory Reports  
* Customer Reports  
* Revenue Dashboard  
* Export Reports

### **Key User Stories**

## **US-RPT-001 — Sales Dashboard**

> As an administrator, I want to view sales metrics so that I can monitor business performance.

---

## **US-RPT-002 — Inventory Report**

> As an inventory manager, I want to identify slow-moving and low-stock products so that I can optimize inventory planning.

---

## **US-RPT-003 — Customer Insights**

> As a marketing manager, I want customer purchasing insights so that I can plan targeted campaigns.

---

# **EP-18: Vendor Marketplace (Future)**

## **Epic Overview**

**Epic ID:** EP-18  
**Priority:** Won't Have (MVP)

### **Goal**

Expand The Shatranj Heritage into a marketplace where artisans and merchants can sell chess-related products.

## **Planned Features**

* Vendor registration  
* Vendor verification  
* Vendor dashboard  
* Product management  
* Commission management  
* Vendor payouts  
* Vendor analytics

### **Example User Story**

## **US-VND-001 — Register as Vendor**

> As an artisan, I want to register as a vendor so that I can sell handcrafted chess products through The Shatranj Heritage.

---

# **Story Dependency Matrix (Sample)**

| Story | Depends On |
| ----- | ----- |
| US-AUTH-003 (Login) | US-AUTH-001 / US-AUTH-002 |
| US-CRT-001 (Add to Cart) | US-CAT-001 (Browse Products) |
| US-CHK-001 (Checkout) | US-CRT-004 (View Cart) |
| US-PAY-001 (Online Payment) | US-CHK-006 (Place Order) |
| US-ORD-002 (Track Order) | US-ORD-001 (Create Order) |
| US-SHP-003 (Track Shipment) | US-SHP-002 (Assign Courier) |

---

# **MVP Release Mapping**

## **MVP (Version 1)**

### **Customer Experience**

* Authentication  
* Customer Profiles  
* Product Catalog  
* Search  
* Shopping Cart  
* Checkout  
* Payment  
* Orders  
* Shipping  
* Notifications

### **Administration**

* Product Management  
* Inventory  
* Orders  
* Customers  
* Reports  
* Basic CMS

---

## **Version 2**

* Wishlist  
* Reviews  
* Promotions  
* Advanced CMS  
* Customer Preferences  
* Refund Management  
* Buying Guides  
* Blog  
* Loyalty Program (Optional)

---

## **Version 3**

* Vendor Marketplace  
* Mobile Applications  
* AI Recommendations  
* Product Comparison  
* Regional Expansion  
* International Shipping

---

# **Requirements Traceability Matrix (Sample)**

| Product Vision | BRD | SRS | Epic | Sample Story |
| ----- | ----- | ----- | ----- | ----- |
| Promote local craftsmanship | BR-05 | FR-CAT-008 | EP-03 | US-CAT-006 |
| Deliver seamless purchasing | BR-09 | FR-CHK-001 | EP-07 | US-CHK-006 |
| Support Bangladeshi payments | BR-11 | FR-PAY-001 | EP-08 | US-PAY-001 |
| Build customer trust | BR-14 | FR-REV-001 | EP-11 | US-REV-001 |
| Enable operational efficiency | BR-17 | FR-ADM-001 | EP-13 | US-ADM-001 |

---

# **Product Backlog Summary**

| Epic | Priority | Release |
| ----- | ----- | ----- |
| EP-01 Authentication & Authorization | Must | MVP |
| EP-02 Customer Management | Must | MVP |
| EP-03 Product Catalog | Must | MVP |
| EP-04 Search & Discovery | Must | MVP |
| EP-05 Shopping Cart | Must | MVP |
| EP-06 Wishlist | Should | V2 |
| EP-07 Checkout | Must | MVP |
| EP-08 Payment Management | Must | MVP |
| EP-09 Order Management | Must | MVP |
| EP-10 Shipping & Fulfillment | Must | MVP |
| EP-11 Reviews & Ratings | Should | V2 |
| EP-12 Notifications | Must | MVP |
| EP-13 Administration | Must | MVP |
| EP-14 Inventory Management | Must | MVP |
| EP-15 Promotions & Discounts | Should | V2 |
| EP-16 Content Management System | Should | V2 |
| EP-17 Reporting & Analytics | Must | MVP |
| EP-18 Vendor Marketplace | Won't | V3 |

---

# **Backlog Statistics**

* **Total Epics:** 18  
* **Estimated Features:** \~90  
* **Estimated User Stories:** \~220–250  
* **MVP Coverage:** 60–70% of the total backlog  
* **Future Releases:** V2 (engagement and content), V3 (marketplace and regional expansion)

---

# **Final Remarks**

This Product Backlog is intentionally structured to bridge strategy and execution:

* The **Product Vision** defines *why* The Shatranj Heritage exists.  
* The **BRD** captures *what the business needs*.  
* The **SRS** specifies *how the software should behave*.  
* The **Product Backlog & User Stories** define *the work required to build it*.


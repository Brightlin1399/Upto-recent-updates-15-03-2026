from pydantic import BaseModel
from typing import Optional

class SubmitPCRRequest(BaseModel):
    submitted_by: int
    pcr_id: str
    country: str
    brand: str
    product_skus: list[str] = []
    product_name: Optional[str] = None
    product_id: Optional[str] = None
    proposed_price: Optional[str] = None
    channel: Optional[str] = "Retail"
    price_type: Optional[str] = "NSP Minimum"
    price_change_type: Optional[str] = None
    expected_response_date: Optional[str] = None
    price_change_reason: Optional[str] = None
    price_change_reason_comments: Optional[str] = None
    submission_context: Optional[str] = None
    proposed_percent: Optional[str] = None
    is_discontinue_price: Optional[bool] = None
    effective_date: Optional[str] = None
    save_as_draft: Optional[bool] = False  # if True, store as draft without submitting
class ApproveRejectRequest(BaseModel):
    approved_by: Optional[int] =None
    rejected_by: Optional[int] =None
class UpdatePCRRequest(BaseModel):
    edited_by: int
    pcr_id_display: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    current_price: Optional[str] = None
    proposed_price: Optional[str] = None
    price_change_type: Optional[str] = None
    expected_response_date: Optional[str] = None
    price_change_reason: Optional[str] = None
    price_change_reason_comments: Optional[str] = None
    submission_context: Optional[str] = None
    product_skus: Optional[str] = None
    proposed_percent: Optional[str] = None
    is_discontinue_price: Optional[bool] = None
    effective_date: Optional[str] = None
    price_type: Optional[str] = None
class RegionalEditPCRRequest(BaseModel):
    edited_by: int
    price_change_type: Optional[str] = None
    expected_response_date: Optional[str] = None
    price_change_reason: Optional[str] = None
    price_change_reason_comments: Optional[str] = None
    submission_context: Optional[str] = None
    product_skus: Optional[str] = None
    proposed_percent: Optional[str] = None
    is_discontinue_price: Optional[bool] = None
    effective_date: Optional[str] = None

class ResubmitPCRRequest(BaseModel):
    re_submitted_by:int
class EscalateToGlobalRequest(BaseModel):
    escalated_by: int
class MessageResponse(BaseModel):
    message:str
    pcr_id:str
class ErrorResponse(BaseModel):
    error:str

class DirectChatCreate(BaseModel):
    user_id: int  # the other user

class GroupChatCreate(BaseModel):
    name: Optional[str] = None
    member_ids: list[int]  # user ids to add (creator added automatically)

class SendMessageRequest(BaseModel):
    body: str

class FinalisePCRRequest(BaseModel):
    finalised_by: int
    published: Optional[bool] = None  # yes/no; logic to set/use it will be implemented later


# Admin user management
class CreateUserRequest(BaseModel):
    name: str
    email: str
    role: str  # Local | Regional | Global | Admin
    country: Optional[str] = None
    therapeutic_area: Optional[str] = None
    region: Optional[str] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None  # Local | Regional | Global | Admin
    country: Optional[str] = None
    therapeutic_area: Optional[str] = None
    region: Optional[str] = None


# Master data: Admin CRUD on sku_mdgm_master (create/update/delete SKU rows).
# Unique key: (sku_id, country, channel, price_type). NOT NULL: country, therapeutic_area, brand, channel, sku_id.
class CreateMDGMRequest(BaseModel):
    """Admin: create one MDGM row. All columns supported."""
    sku_id: str
    country: str
    therapeutic_area: str
    brand: str
    channel: str = "Retail"
    price_type: Optional[str] = None
    region: Optional[str] = None
    global_product_name: Optional[str] = None
    local_product_name: Optional[str] = None
    pu: Optional[int] = None
    measure: Optional[str] = None
    dimension: Optional[str] = None
    volume_of_container: Optional[str] = None
    container: Optional[str] = None
    strength: Optional[str] = None
    currency: Optional[str] = None
    erp_applicable: Optional[str] = None
    pack_size: Optional[int] = None
    reimbursement_price_local: Optional[float] = None
    reimbursement_price_eur: Optional[float] = None
    reimbursement_status: Optional[str] = None
    reimbursement_rate: Optional[float] = None
    marketed_status: Optional[str] = None
    current_price_eur: Optional[float] = None


class UpdateMDGMRequest(BaseModel):
    """Admin: update an MDGM row by id. All fields optional; only provided fields are updated."""
    sku_id: Optional[str] = None
    country: Optional[str] = None
    therapeutic_area: Optional[str] = None
    brand: Optional[str] = None
    channel: Optional[str] = None
    price_type: Optional[str] = None
    region: Optional[str] = None
    global_product_name: Optional[str] = None
    local_product_name: Optional[str] = None
    pu: Optional[int] = None
    measure: Optional[str] = None
    dimension: Optional[str] = None
    volume_of_container: Optional[str] = None
    container: Optional[str] = None
    strength: Optional[str] = None
    currency: Optional[str] = None
    erp_applicable: Optional[str] = None
    pack_size: Optional[int] = None
    reimbursement_price_local: Optional[float] = None
    reimbursement_price_eur: Optional[float] = None
    reimbursement_status: Optional[str] = None
    reimbursement_rate: Optional[float] = None
    marketed_status: Optional[str] = None
    current_price_eur: Optional[float] = None
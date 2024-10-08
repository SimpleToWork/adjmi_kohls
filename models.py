from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Charge(Base):
	__tablename__ = 'charge'

	id = Column(Integer, primary_key=True)
	charge_type_desc = Column(String(200), nullable=True)
	original_charge_amt = Column(Float, nullable=True)
	service_fee = Column(Float, nullable=True)
	amount = Column(Float, nullable=True)
	po = Column(Integer, nullable=True)
	transmitted = Column(DateTime, nullable=True)
	cust_rule = Column(String(100), nullable=True)
	rule_description = Column(String(255), nullable=True)
	rule = Column(Integer, nullable=True)
	category_desc = Column(String(255), nullable=True)
	audit_source = Column(String(255), nullable=True)
	status = Column(String(100), nullable=True)
	tier = Column(Integer, nullable=True)
	dc_store = Column(Integer, nullable=True)
	site_name = Column(String(150), nullable=True)
	vendor = Column(Integer, nullable=True)
	vendor_name = Column(String(150), nullable=True)
	bill_type = Column(String(100), nullable=True)
	pro_bill_type_desc = Column(String(255), nullable=True)
	trouble_user_def1 = Column(String(200), nullable=True)
	trouble_user_def2 = Column(String(200), nullable=True)
	po_asn_count = Column(Integer, nullable=True)
	parent_company = Column(String(150), nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	audit_troubles = relationship("AuditTrouble", back_populates="charge")
	audit_issues = relationship("AuditIssue", back_populates="charge")
	documents = relationship("Document", back_populates="charge")
	emails = relationship("Email", back_populates="charge")
	fill_details = relationship("FillDetail", back_populates="charge")
	po_receivers = relationship("PoReceiver", back_populates="charge")
	reports = relationship("Report", back_populates="charge")
	routing_requests_1 = relationship("RoutingRequest1", back_populates="charge")
	routing_requests_2 = relationship("RoutingRequest2", back_populates="charge")

	def __repr__(self):
		return f"<Charge(id={self.id})>"


class AuditTrouble(Base):
	__tablename__ = "audit_trouble"

	id = Column(Integer, primary_key=True, autoincrement=True)
	source = Column(String(150), nullable=True)
	audit_number = Column(Integer, nullable=True)
	trouble_number = Column(Integer, nullable=True)
	description = Column(String(255), nullable=True)
	entry_date = Column(DateTime, nullable=True)
	comments = Column(String(255), nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates="audit_troubles")


class AuditIssue(Base):
	__tablename__ = 'audit_issue'

	id = Column(Integer, primary_key=True, autoincrement=True)
	rule_num = Column(Integer, nullable=True)
	issue = Column(Integer, nullable=True)
	style = Column(String(100), nullable=True)
	item = Column(String(100), nullable=True)
	units = Column(String(100), nullable=True)
	cartons = Column(Float, nullable=True)
	gs1128 = Column(String(100), nullable=True)
	comments = Column(String(255), nullable=True)
	sku = Column(String(100), nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates="audit_issues")


class Document(Base):
	__tablename__ = "document"

	id = Column(Integer, primary_key=True, autoincrement=True)
	document_name = Column(String(255), nullable=True)
	thumbnail = Column(String(255), nullable=True)
	po = Column(Integer, nullable=True)
	receiver = Column(String(200), nullable=True)
	trouble = Column(String(200), nullable=True)
	audit = Column(Integer, nullable=True)
	audit_sequence = Column(Integer, nullable=True)
	trailer = Column(String(200), nullable=True)
	scac = Column(String(200), nullable=True)
	location = Column(String(200), nullable=True)
	received = Column(String(200), nullable=True)
	pro = Column(String(200), nullable=True)
	document_size = Column(Float, nullable=True)
	dispute = Column(String(200), nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates="documents")


class Email(Base):
	__tablename__ = "email"

	id = Column(Integer, primary_key=True, autoincrement=True)
	queued_date = Column(DateTime, nullable=True)
	generated_date = Column(DateTime, nullable=True)
	to = Column(String(200), nullable=True)
	cc = Column(String(200), nullable=True)
	bcc = Column(String(200), nullable=True)
	subject = Column(String(255), nullable=True)
	reports = Column(Integer, nullable=True)
	documents = Column(Integer, nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates='emails')


class FillDetail(Base):
	__tablename__ = "fill_detail"

	id = Column(Integer, primary_key=True, autoincrement=True)
	style = Column(Integer, nullable=True)
	sku = Column(Integer, nullable=True)
	upc = Column(Integer, nullable=True)
	units_ordered = Column(Integer, nullable=True)
	units_received = Column(Integer, nullable=True)
	units_over_short = Column(Integer, nullable=True)
	fill_rate = Column(Integer, nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates='fill_details')


class PoReceiver(Base):
	__tablename__ = 'po_receiver'

	id = Column(Integer, primary_key=True, autoincrement=True)
	receiver_number = Column(Integer, nullable=True)
	receive_date = Column(DateTime, nullable=True)
	cartons = Column(Integer, nullable=True)
	units = Column(Integer, nullable=True)
	cost = Column(Float, nullable=True)
	retail = Column(Float, nullable=True)
	po = Column(Integer, nullable=True)
	po_units = Column(Integer, nullable=True)
	po_cost = Column(Float, nullable=True)
	po_retail = Column(Float, nullable=True)
	department = Column(Integer, nullable=True)
	start_ship = Column(DateTime, nullable=True)
	stop_ship = Column(DateTime, nullable=True)
	vendor = Column(String(250), nullable=True)
	vendor_num = Column(Integer, nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates='po_receivers')


class Report(Base):
	__tablename__ = 'report'

	id = Column(Integer, primary_key=True, autoincrement=True)
	file_name = Column(String(255), nullable=True)
	created = Column(DateTime, nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates='reports')


class RoutingRequest1(Base):
	__tablename__ = 'routing_request_1'

	id = Column(Integer, primary_key=True, autoincrement=True)
	pro_num = Column(String(120), nullable=True)
	shipper = Column(String(200), nullable=True)
	authorization_num = Column(Integer, nullable=True)
	hdr_expected_ctns = Column(Integer, nullable=True)
	hdr_weight = Column(Float, nullable=True)
	hdr_routing_request_dt = Column(DateTime, nullable=True)
	hdr_ready_for_pickup_dt = Column(DateTime, nullable=True)
	hdr_stop_pickup_dt = Column(DateTime, nullable=True)
	hdr_start_delivery_dt = Column(DateTime, nullable=True)
	hdr_stop_delivery_dt = Column(DateTime, nullable=True)
	hdr_appt_dt = Column(DateTime, nullable=True)
	hdr_freight_class = Column(String(200), nullable=True)
	hdr_origin_location = Column(String(150), nullable=True)
	hdr_origin_city = Column(String(160), nullable=True)
	hdr_origin_st = Column(String(100), nullable=True)
	hdr_origin_zip = Column(Integer, nullable=True)
	hdr_stop_number = Column(Integer, nullable=True)
	hdr_destination_location = Column(String(150), nullable=True)
	hdr_dest_state = Column(String(100), nullable=True)
	hdr_multi_stop_fl = Column(String(200), nullable=True)
	hdr_floor_load = Column(String(200), nullable=True)
	hdr_complete_ts = Column(DateTime, nullable=True)
	hdr_update_ts = Column(DateTime, nullable=True)
	hdr_request_granted_dt = Column(DateTime, nullable=True)
	hdr_cms_create_ts = Column(DateTime, nullable=True)
	hdr_cms_analysis_ts = Column(DateTime, nullable=True)
	hdr_pallets = Column(String(200), nullable=True)
	hdr_cube = Column(Integer, nullable=True)
	hdr_dest = Column(Integer, nullable=True)
	release_dt = Column(DateTime, nullable=True)
	ship_start_dt = Column(DateTime, nullable=True)
	release_days = Column(Integer, nullable=True)
	routing_request_dt = Column(DateTime, nullable=True)
	routing_days_from_start = Column(Integer, nullable=True)
	ship_stop_dt = Column(DateTime, nullable=True)
	late_ship_dt = Column(DateTime, nullable=True)
	po_num = Column(Integer, nullable=True)
	po_ctns = Column(Integer, nullable=True)
	cube = Column(Integer, nullable=True)
	weight = Column(Float, nullable=True)
	pallets = Column(Integer, nullable=True)
	pallet_position_qty = Column(Integer, nullable=True)
	loading_order = Column(Integer, nullable=True)
	dispatched_dt = Column(DateTime, nullable=True)
	tendered_dt = Column(DateTime, nullable=True)
	accepted_dt = Column(DateTime, nullable=True)
	en_route_dt = Column(DateTime, nullable=True)
	final_destination_dt = Column(DateTime, nullable=True)
	shipment_cost = Column(Float, nullable=True)
	cancelled_dt = Column(DateTime, nullable=True)
	cms_update_ts = Column(DateTime, nullable=True)
	cms_create_ts = Column(DateTime, nullable=True)
	ready_for_pickup_dt = Column(DateTime, nullable=True)
	start_delivery_dt = Column(DateTime, nullable=True)
	stop_delivery_dt = Column(DateTime, nullable=True)
	appt_dt = Column(DateTime, nullable=True)
	request_granted_dt = Column(DateTime, nullable=True)
	early_available_dt = Column(DateTime, nullable=True)
	transit_days = Column(Integer, nullable=True)
	routing_request_id = Column(Integer, nullable=True)
	vendor_routed = Column(String(200), nullable=True)
	delete_code = Column(String(200), nullable=True)
	appointment_id = Column(String(200), nullable=True)
	floor_load = Column(String(40), nullable=True)
	freight_class = Column(Integer, nullable=True)
	origin_location = Column(String(150), nullable=True)
	origin_city = Column(String(160), nullable=True)
	origin_state = Column(String(100), nullable=True)
	origin_zip = Column(Integer, nullable=True)
	stop_number = Column(String(200), nullable=True)
	destination_location = Column(String(160), nullable=True)
	destination_state = Column(String(100), nullable=True)
	multi_stop_fl = Column(String(40), nullable=True)
	po_routed_units = Column(Integer, nullable=True)
	dest = Column(Integer, nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates='routing_requests_1')


class RoutingRequest2(Base):
	__tablename__ = 'routing_request_2'

	id = Column(Integer, primary_key=True, autoincrement=True)
	dest_loc_num = Column(Integer, nullable=True)
	charge_number = Column(Integer, ForeignKey('charge.id'))

	charge = relationship("Charge", back_populates='routing_requests_2')
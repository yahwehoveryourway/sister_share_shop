import os
from datetime import datetime, date
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_, func
from app import app, db
from models import User, Category, Donation, Request, Match, Notification
from forms import LoginForm, RegistrationForm, DonationForm, RequestForm, ApprovalForm, MatchForm, CategoryForm
from email_service import send_thank_you_email, send_match_notification

@app.route('/')
def index():
    recent_donations = Donation.query.filter_by(status='approved').order_by(Donation.approved_at.desc()).limit(6).all()
    urgent_requests = Request.query.filter_by(status='active', urgency='urgent').order_by(Request.created_at.desc()).limit(3).all()
    categories = Category.query.all()
    return render_template('index.html', recent_donations=recent_donations, urgent_requests=urgent_requests, categories=categories)

@app.route('/browse')
def browse_donations():
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of items per page
    
    # Start with base query for approved donations
    query = Donation.query.filter_by(status='approved')
    
    # Search by title or description
    search_term = request.args.get('search', '').strip()
    if search_term:
        query = query.filter(
            or_(
                Donation.title.ilike(f'%{search_term}%'),
                Donation.description.ilike(f'%{search_term}%')
            )
        )
    
    # Filter by category
    category_id = request.args.get('category', type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Filter by items with photos
    has_photo = request.args.get('has_photo')
    if has_photo:
        query = query.filter(Donation.photo_filename.isnot(None))
    
    # Date range filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(func.date(Donation.approved_at) >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(func.date(Donation.approved_at) <= to_date)
        except ValueError:
            pass
    
    # Sorting
    sort_option = request.args.get('sort', 'newest')
    if sort_option == 'oldest':
        query = query.order_by(Donation.approved_at.asc())
    elif sort_option == 'title_asc':
        query = query.order_by(Donation.title.asc())
    elif sort_option == 'title_desc':
        query = query.order_by(Donation.title.desc())
    else:  # newest (default)
        query = query.order_by(Donation.approved_at.desc())
    
    # Get total count for results summary
    total_count = query.count()
    
    # Paginate results
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    donations = pagination.items
    
    # Get all categories for filter dropdown
    categories = Category.query.order_by(Category.name).all()
    
    return render_template('browse_donations.html', 
                         donations=donations,
                         categories=categories,
                         total_count=total_count,
                         pagination=pagination)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/donor_portal')
@login_required
def donor_portal():
    donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()
    requests = Request.query.filter_by(requester_id=current_user.id).order_by(Request.created_at.desc()).all()
    return render_template('donor_portal.html', donations=donations, requests=requests)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    pending_donations = Donation.query.filter_by(status='pending').order_by(Donation.created_at.desc()).all()
    active_requests = Request.query.filter_by(status='active').order_by(Request.created_at.desc()).all()
    recent_matches = Match.query.order_by(Match.created_at.desc()).limit(10).all()
    
    stats = {
        'total_donations': Donation.query.count(),
        'pending_donations': Donation.query.filter_by(status='pending').count(),
        'approved_donations': Donation.query.filter_by(status='approved').count(),
        'donated_items': Donation.query.filter_by(status='donated').count(),
        'active_requests': Request.query.filter_by(status='active').count(),
        'total_matches': Match.query.count()
    }
    
    return render_template('admin_dashboard.html', 
                         pending_donations=pending_donations,
                         active_requests=active_requests,
                         recent_matches=recent_matches,
                         stats=stats)

@app.route('/donate', methods=['GET', 'POST'])
@login_required
def donate_item():
    form = DonationForm()
    if form.validate_on_submit():
        donation = Donation(
            title=form.title.data,
            description=form.description.data,
            category_id=form.category_id.data,
            donor_id=current_user.id
        )
        
        # Handle file upload
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)
            # Add timestamp to avoid filename conflicts
            filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.photo.data.save(filepath)
            donation.photo_filename = filename
        
        db.session.add(donation)
        db.session.commit()
        
        # Create notification for admins
        admins = User.query.filter_by(is_admin=True).all()
        for admin in admins:
            notification = Notification(
                title='New Donation Submitted',
                message=f'New donation "{donation.title}" by {current_user.username}',
                type='info',
                user_id=admin.id
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Thank you for your donation! It will be reviewed by our team.', 'success')
        return redirect(url_for('donor_portal'))
    
    return render_template('donate_item.html', form=form)

@app.route('/request', methods=['GET', 'POST'])
@login_required
def request_item():
    form = RequestForm()
    if form.validate_on_submit():
        item_request = Request(
            title=form.title.data,
            description=form.description.data,
            category_id=form.category_id.data,
            urgency=form.urgency.data,
            requester_id=current_user.id
        )
        
        db.session.add(item_request)
        db.session.commit()
        
        # Create notification for admins
        admins = User.query.filter_by(is_admin=True).all()
        for admin in admins:
            notification = Notification(
                title='New Item Request',
                message=f'New request "{item_request.title}" by {current_user.username}',
                type='info',
                user_id=admin.id
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Your request has been submitted successfully!', 'success')
        return redirect(url_for('donor_portal'))
    
    return render_template('request_item.html', form=form)

@app.route('/item/<int:id>')
def item_detail(id):
    donation = Donation.query.get_or_404(id)
    
    # Check if user can view this donation
    if not current_user.is_authenticated:
        # Non-authenticated users can only view approved donations
        if donation.status != 'approved':
            flash('This item is not available for viewing.', 'warning')
            return redirect(url_for('login'))
    elif not current_user.is_admin and donation.donor_id != current_user.id and donation.status != 'approved':
        flash('You do not have permission to view this item.', 'danger')
        return redirect(url_for('index'))
    
    # Get related items from same category
    related_items = Donation.query.filter(
        and_(
            Donation.category_id == donation.category_id,
            Donation.id != donation.id,
            Donation.status == 'approved'
        )
    ).order_by(Donation.approved_at.desc()).limit(4).all()
    
    return render_template('item_detail.html', donation=donation, related_items=related_items)

@app.route('/approve_donation/<int:id>', methods=['POST'])
@login_required
def approve_donation(id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    donation = Donation.query.get_or_404(id)
    form = ApprovalForm()
    
    if form.validate_on_submit():
        donation.status = form.status.data
        donation.approved_by_id = current_user.id
        donation.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        # Create notification for donor
        notification = Notification(
            title=f'Donation {form.status.data.title()}',
            message=f'Your donation "{donation.title}" has been {form.status.data}.',
            type='success' if form.status.data == 'approved' else 'warning',
            user_id=donation.donor_id
        )
        db.session.add(notification)
        db.session.commit()
        
        # If approved, check for potential matches
        if form.status.data == 'approved':
            check_for_matches(donation)
        
        flash(f'Donation has been {form.status.data}.', 'success')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/create_match/<int:donation_id>/<int:request_id>', methods=['POST'])
@login_required
def create_match(donation_id, request_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    donation = Donation.query.get_or_404(donation_id)
    item_request = Request.query.get_or_404(request_id)
    
    # Check if match already exists
    existing_match = Match.query.filter_by(donation_id=donation_id, request_id=request_id).first()
    if existing_match:
        flash('Match already exists for these items.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    match = Match(
        donation_id=donation_id,
        request_id=request_id,
        matched_by_id=current_user.id,
        status='approved'
    )
    
    # Update statuses
    donation.status = 'donated'
    donation.donated_at = datetime.utcnow()
    item_request.status = 'fulfilled'
    item_request.fulfilled_at = datetime.utcnow()
    
    db.session.add(match)
    db.session.commit()
    
    # Send notifications
    send_match_notification(donation, item_request, match)
    
    # Send thank you email to donor
    if not donation.thank_you_sent:
        send_thank_you_email(donation)
        donation.thank_you_sent = True
        db.session.commit()
    
    flash('Match created successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

def check_for_matches(donation):
    """Check for potential matches between approved donation and active requests"""
    potential_requests = Request.query.filter_by(
        category_id=donation.category_id,
        status='active'
    ).all()
    
    for req in potential_requests:
        # Create notification for admin about potential match
        admins = User.query.filter_by(is_admin=True).all()
        for admin in admins:
            notification = Notification(
                title='Potential Match Found',
                message=f'Donation "{donation.title}" may match request "{req.title}"',
                type='info',
                user_id=admin.id
            )
            db.session.add(notification)
    
    if potential_requests:
        db.session.commit()

# Initialize default categories and admin user
def create_default_data():
    # Create default categories
    default_categories = [
        {'name': 'Clothing', 'description': 'Clothes, shoes, accessories'},
        {'name': 'Household Items', 'description': 'Furniture, kitchenware, decorations'},
        {'name': 'Electronics', 'description': 'Phones, computers, appliances'},
        {'name': 'Books & Media', 'description': 'Books, movies, games'},
        {'name': 'Toys & Games', 'description': 'Children\'s toys and games'},
        {'name': 'Personal Care', 'description': 'Hygiene products, cosmetics'},
        {'name': 'Food & Supplies', 'description': 'Non-perishable food items'},
        {'name': 'Other', 'description': 'Items that don\'t fit other categories'}
    ]
    
    for cat_data in default_categories:
        if not Category.query.filter_by(name=cat_data['name']).first():
            category = Category(**cat_data)
            db.session.add(category)
    
    # Create default admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@sistershare.org',
            is_admin=True
        )
        admin.set_password('admin123')  # Change this in production
        db.session.add(admin)
    
    db.session.commit()

# This will be called after database tables are created

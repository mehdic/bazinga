---
name: rails
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [ruby]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Ruby on Rails Engineering Expertise

## Specialist Profile
Rails specialist building rapid web applications. Expert in ActiveRecord, concerns, and the Rails way.

## Implementation Guidelines

### Models

```ruby
class User < ApplicationRecord
  # Associations
  has_many :orders, dependent: :destroy
  has_one :profile, dependent: :destroy
  belongs_to :organization, optional: true

  # Validations
  validates :email, presence: true, uniqueness: { case_sensitive: false },
                    format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :display_name, presence: true, length: { minimum: 2, maximum: 100 }

  # Scopes
  scope :active, -> { where(status: :active) }
  scope :recent, -> { order(created_at: :desc) }
  scope :with_orders, -> { includes(:orders).where.not(orders: { id: nil }) }

  # Enums
  enum status: { active: 0, inactive: 1, pending: 2 }

  # Callbacks
  before_create :set_defaults
  after_create_commit :send_welcome_email

  private

  def set_defaults
    self.status ||= :pending
  end

  def send_welcome_email
    UserMailer.welcome(self).deliver_later
  end
end
```

### Controllers

```ruby
class Api::V1::UsersController < ApplicationController
  before_action :set_user, only: [:show, :update, :destroy]

  def index
    @users = User.active.recent.page(params[:page])
    render json: UserSerializer.new(@users).serializable_hash
  end

  def show
    render json: UserSerializer.new(@user).serializable_hash
  end

  def create
    @user = User.new(user_params)

    if @user.save
      render json: UserSerializer.new(@user).serializable_hash, status: :created
    else
      render json: { errors: @user.errors }, status: :unprocessable_entity
    end
  end

  private

  def set_user
    @user = User.find(params[:id])
  end

  def user_params
    params.require(:user).permit(:email, :display_name)
  end
end
```

### Service Objects

```ruby
class Users::Create
  def initialize(params:, current_user: nil)
    @params = params
    @current_user = current_user
  end

  def call
    user = User.new(@params)

    ActiveRecord::Base.transaction do
      user.save!
      create_profile(user)
      notify_admin(user)
    end

    Success(user)
  rescue ActiveRecord::RecordInvalid => e
    Failure(e.record.errors)
  end

  private

  def create_profile(user)
    Profile.create!(user: user)
  end

  def notify_admin(user)
    AdminNotifier.new_user(user).deliver_later
  end
end
```

### Concerns

```ruby
# app/models/concerns/searchable.rb
module Searchable
  extend ActiveSupport::Concern

  included do
    scope :search, ->(query) {
      return all if query.blank?
      where('name ILIKE :q OR email ILIKE :q', q: "%#{query}%")
    }
  end
end

# Usage
class User < ApplicationRecord
  include Searchable
end
```

### Background Jobs

```ruby
class SendWelcomeEmailJob < ApplicationJob
  queue_as :default
  retry_on Net::SMTPError, wait: 5.seconds, attempts: 3

  def perform(user_id)
    user = User.find(user_id)
    UserMailer.welcome(user).deliver_now
  end
end
```

## Patterns to Avoid
- ❌ Fat controllers (use services)
- ❌ N+1 queries (use includes/preload)
- ❌ Callbacks for business logic
- ❌ Skip validations

## Verification Checklist
- [ ] Proper validations
- [ ] Scopes for queries
- [ ] Service objects for complex logic
- [ ] Background jobs for async
- [ ] RSpec tests with FactoryBot

'use client';

import { useState, useMemo } from 'react';
import Header from '@/components/ui/Header';
import FloatingChatBot from '@/components/ui/FloatingChatBot';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ExclamationCircleIcon,
  UserCircleIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  DocumentTextIcon,
  PhoneIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { format, addDays, subDays } from 'date-fns';
import { useEngageAppointments, useCheckInAppointment, ServiceAppointment } from '@/lib/api/engageDashboard';

// Transform backend appointment to frontend format
const transformAppointment = (apt: ServiceAppointment) => ({
  id: apt.id.toString(),
  time: apt.appointment_time,
  vehicle: {
    year: apt.vehicle_year,
    make: apt.vehicle_make,
    model: apt.vehicle_model || '',
    vin: apt.vehicle_vin,
    mileage: apt.vehicle_mileage || '',
    iconColor: apt.vehicle_icon_color,
  },
  customer: {
    name: apt.customer_name,
    phone: apt.phone,
    email: apt.email,
    loyaltyTier: apt.loyalty_tier,
    preferredServices: apt.preferred_services || [],
    serviceHistory: apt.service_history_count || 0,
    lastVisit: apt.last_visit_date,
  },
  advisor: apt.advisor,
  secondaryContact: apt.secondary_contact,
  status: apt.status,
  roNumber: apt.ro_number,
  code: apt.code,
  estimatedDuration: apt.estimated_duration,
  serviceType: apt.service_type,
  notes: apt.notes,
});

const statusConfig = {
  not_arrived: {
    label: 'Not Arrived',
    bg: 'bg-white',
    border: 'border-gray-200',
    icon: ClockIcon,
    color: 'text-gray-600',
  },
  checked_in: {
    label: 'Checked In',
    bg: 'bg-green-50',
    border: 'border-green-300',
    icon: CheckCircleIcon,
    color: 'text-green-700',
  },
  in_progress: {
    label: 'In Progress',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    icon: ClockIcon,
    color: 'text-blue-700',
  },
  completed: {
    label: 'Completed',
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    color: 'text-green-700',
  },
  cancelled: {
    label: 'Cancelled',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: XCircleIcon,
    color: 'text-red-700',
  },
};

const iconColors = {
  blue: 'text-blue-600',
  red: 'text-red-600',
  gray: 'text-gray-400',
};

export default function EngagePage() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [advisorFilter, setAdvisorFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAppointment, setSelectedAppointment] = useState<any | null>(null);
  const [showCheckInModal, setShowCheckInModal] = useState(false);

  const checkInMutation = useCheckInAppointment();

  // Fetch appointments from backend
  const { data, isLoading, error } = useEngageAppointments({
    date: format(selectedDate, 'yyyy-MM-dd'),
    advisor: advisorFilter,
    status: statusFilter,
    search: searchQuery || undefined,
  });

  const needsActionCount = data?.needs_action_count || 0;
  const appointments = data?.appointments || [];

  // Transform backend appointments to frontend format
  const transformedAppointments = useMemo(() => {
    return appointments.map(transformAppointment);
  }, [appointments]);

  // Group appointments by time
  const appointmentsByTime = useMemo(() => {
    const grouped: Record<string, any[]> = {};
    transformedAppointments.forEach(apt => {
      if (!grouped[apt.time]) {
        grouped[apt.time] = [];
      }
      grouped[apt.time].push(apt);
    });
    return grouped;
  }, [transformedAppointments]);

  // Get unique advisors
  const advisors = useMemo(() => {
    return Array.from(new Set(transformedAppointments.map(apt => apt.advisor)));
  }, [transformedAppointments]);

  const statuses = ['All', 'not_arrived', 'checked_in', 'in_progress', 'completed', 'cancelled'];

  const handleCheckIn = (appointment: ServiceAppointment) => {
    setSelectedAppointment(appointment);
    setShowCheckInModal(true);
  };

  const handleCompleteCheckIn = async () => {
    if (selectedAppointment) {
      try {
        await checkInMutation.mutateAsync(parseInt(selectedAppointment.id));
        setShowCheckInModal(false);
        setSelectedAppointment(null);
      } catch (error) {
        console.error('Failed to check in appointment:', error);
        // You could add a toast notification here
      }
    }
  };

  const handlePreviousDay = () => {
    setSelectedDate(prev => subDays(prev, 1));
  };

  const handleNextDay = () => {
    setSelectedDate(prev => addDays(prev, 1));
  };

  const handleToday = () => {
    setSelectedDate(new Date());
  };

  // Prepare page context for the bot
  const pageContext = useMemo(() => {
    return {
      page: 'Engage - Customer Experience Management',
      schedule: {
        date: format(selectedDate, 'MMM d, yyyy'),
        totalAppointments: transformedAppointments.length,
        byStatus: {
          notArrived: transformedAppointments.filter(a => a.status === 'not_arrived').length,
          checkedIn: transformedAppointments.filter(a => a.status === 'checked_in').length,
          inProgress: transformedAppointments.filter(a => a.status === 'in_progress').length,
          completed: transformedAppointments.filter(a => a.status === 'completed').length,
        },
        appointments: transformedAppointments.slice(0, 10).map(apt => ({
          time: apt.time,
          vehicle: `${apt.vehicle.year} ${apt.vehicle.make}`,
          customer: apt.customer.name,
          customerTier: apt.customer.loyaltyTier,
          phone: apt.customer.phone,
          email: apt.customer.email,
          serviceHistory: apt.customer.serviceHistory,
          preferredServices: apt.customer.preferredServices,
          advisor: apt.advisor,
          status: apt.status,
          roNumber: apt.roNumber,
          serviceType: apt.serviceType,
          estimatedDuration: apt.estimatedDuration,
        })),
        needsAction: needsActionCount,
      },
    };
  }, [selectedDate, transformedAppointments, needsActionCount]);

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Customer Experience Management"
        subtitle="Cox Automotive • Personalized service experience to speed up the check-in process"
      />
      
      <div className="flex-1 overflow-auto bg-gray-50">
        {/* Header Controls */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            {/* Left side - Date Navigation */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <button
                  onClick={handlePreviousDay}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                  aria-label="Previous day"
                >
                  <ChevronLeftIcon className="w-5 h-5 text-gray-600" />
                </button>
                <button
                  onClick={handleToday}
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {format(selectedDate, 'MMM d, yyyy')}
                </button>
                <button
                  onClick={handleNextDay}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                  aria-label="Next day"
                >
                  <ChevronRightIcon className="w-5 h-5 text-gray-600" />
                </button>
              </div>

              <select
                value={advisorFilter}
                onChange={(e) => setAdvisorFilter(e.target.value)}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
              >
                <option value="All">All Advisors</option>
                {advisors.map(advisor => (
                  <option key={advisor} value={advisor}>{advisor}</option>
                ))}
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
              >
                <option value="All">Status</option>
                <option value="not_arrived">Not Arrived</option>
                <option value="checked_in">Checked In</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {/* Right side - Needs Action */}
            <button className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <span>Needs Action</span>
              {needsActionCount > 0 && (
                <span className="flex items-center justify-center w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full">
                  {needsActionCount}
                </span>
              )}
              {needsActionCount === 0 && (
                <span className="flex items-center justify-center w-5 h-5 bg-gray-300 text-white text-xs font-bold rounded-full">
                  0
                </span>
              )}
            </button>
          </div>

          {/* Quick Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by customer name, VIN, vehicle, or RO number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
            />
          </div>
        </div>

        {/* Timeline View */}
        <div className="p-6">
          {isLoading ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Loading appointments...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-500">Error loading appointments. Please try again.</p>
            </div>
          ) : transformedAppointments.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No appointments found for this date</p>
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(appointmentsByTime)
                .sort(([timeA], [timeB]) => {
                  // Sort times chronologically
                  const parseTime = (time: string) => {
                    const [hour, period] = time.split(' ');
                    const [h, m] = hour.split(':');
                    let hour24 = parseInt(h);
                    if (period === 'PM' && hour24 !== 12) hour24 += 12;
                    if (period === 'AM' && hour24 === 12) hour24 = 0;
                    return hour24 * 60 + parseInt(m || '0');
                  };
                  return parseTime(timeA) - parseTime(timeB);
                })
                .map(([time, appointments]) => (
                  <div key={time} className="flex">
                    {/* Time Column */}
                    <div className="w-24 flex-shrink-0 pt-2">
                      <div className="text-sm font-medium text-gray-700">{time}</div>
                    </div>

                    {/* Appointments Column */}
                    <div className="flex-1 space-y-3">
                      {appointments.map((apt) => {
                        const config = statusConfig[apt.status];
                        const iconColor = iconColors[apt.vehicle.iconColor];

                        const StatusIcon = config.icon;
                        const loyaltyBadgeColor = apt.customer.loyaltyTier === 'Platinum' 
                          ? 'bg-purple-100 text-purple-700'
                          : apt.customer.loyaltyTier === 'Gold'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700';

                        return (
                          <div
                            key={apt.id}
                            className={clsx(
                              'rounded-lg border-2 p-4 cursor-pointer hover:shadow-lg transition-all',
                              config.bg,
                              config.border
                            )}
                            onClick={() => setSelectedAppointment(apt)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-start space-x-3 flex-1">
                                {/* Vehicle Icon */}
                                <div className={clsx('flex-shrink-0', iconColor)}>
                                  <svg
                                    className="w-6 h-6"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                                    <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707l-2-2A1 1 0 0015 7h-1z" />
                                  </svg>
                                </div>

                                {/* Appointment Details */}
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 flex-wrap">
                                    <h3 className="font-semibold text-gray-900">
                                      {apt.vehicle.year} {apt.vehicle.make} {apt.vehicle.model}
                                    </h3>
                                    <span className={clsx(
                                      'px-2 py-0.5 text-xs font-medium rounded-full flex items-center space-x-1',
                                      apt.status === 'checked_in' || apt.status === 'in_progress'
                                        ? 'bg-blue-100 text-blue-700'
                                        : apt.status === 'not_arrived'
                                        ? 'bg-gray-100 text-gray-700'
                                        : apt.status === 'completed'
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-red-100 text-red-700'
                                    )}>
                                      <StatusIcon className="w-3 h-3" />
                                      <span>{config.label}</span>
                                    </span>
                                    {apt.customer.loyaltyTier && (
                                      <span className={clsx('px-2 py-0.5 text-xs font-medium rounded-full', loyaltyBadgeColor)}>
                                        {apt.customer.loyaltyTier}
                                      </span>
                                    )}
                                    {apt.roNumber && (
                                      <span className="text-xs text-gray-500 font-mono">
                                        {apt.roNumber}
                                      </span>
                                    )}
                                  </div>
                                  
                                  <div className="mt-2 flex items-center space-x-2">
                                    <UserCircleIcon className="w-4 h-4 text-gray-400" />
                                    <p className="text-sm font-medium text-gray-900">
                                      {apt.customer.name}
                                    </p>
                                  </div>
                                  
                                  <div className="mt-2 space-y-1">
                                    <div className="flex items-center space-x-4 text-xs text-gray-600">
                                      {apt.customer.phone && (
                                        <div className="flex items-center space-x-1">
                                          <PhoneIcon className="w-3 h-3" />
                                          <span>{apt.customer.phone}</span>
                                        </div>
                                      )}
                                      {apt.customer.email && (
                                        <div className="flex items-center space-x-1">
                                          <EnvelopeIcon className="w-3 h-3" />
                                          <span className="truncate max-w-[150px]">{apt.customer.email}</span>
                                        </div>
                                      )}
                                    </div>
                                    
                                    <div className="text-xs text-gray-600">
                                      {apt.vehicle.vin && (
                                        <p>
                                          VIN: {apt.vehicle.vin}
                                          {apt.vehicle.mileage && ` • ${apt.vehicle.mileage}`}
                                        </p>
                                      )}
                                      <div className="flex items-center space-x-3 mt-1">
                                        {apt.serviceType && (
                                          <span className="text-gray-700 font-medium">{apt.serviceType}</span>
                                        )}
                                        {apt.estimatedDuration && (
                                          <span className="text-gray-500">⏱ {apt.estimatedDuration}</span>
                                        )}
                                        {apt.advisor && (
                                          <span className="text-gray-500">👤 {apt.advisor}</span>
                                        )}
                                      </div>
                                      {apt.customer.serviceHistory && (
                                        <p className="mt-1 text-gray-500">
                                          {apt.customer.serviceHistory} previous visits
                                          {apt.customer.lastVisit && ` • Last: ${format(new Date(apt.customer.lastVisit), 'MMM d, yyyy')}`}
                                        </p>
                                      )}
                                    </div>

                                    {/* Preferred Services */}
                                    {apt.customer.preferredServices && apt.customer.preferredServices.length > 0 && (
                                      <div className="mt-2 flex flex-wrap gap-1">
                                        {apt.customer.preferredServices.map((service, idx) => (
                                          <span
                                            key={idx}
                                            className="px-2 py-0.5 text-xs bg-cox-blue-50 text-cox-blue-700 rounded-full"
                                          >
                                            {service}
                                          </span>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* Quick Check-In Button */}
                              {apt.status === 'not_arrived' && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleCheckIn(apt);
                                  }}
                                  className="ml-4 px-4 py-2 bg-cox-blue-600 text-white text-sm font-medium rounded-lg hover:bg-cox-blue-700 transition-colors flex items-center space-x-2"
                                >
                                  <SparklesIcon className="w-4 h-4" />
                                  <span>Quick Check-In</span>
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Check-In Modal */}
      {showCheckInModal && selectedAppointment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900">Quick Check-In</h2>
                <button
                  onClick={() => {
                    setShowCheckInModal(false);
                    setSelectedAppointment(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6">
              {/* Customer Info */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Information</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div>
                    <p className="text-sm text-gray-600">Customer Name</p>
                    <p className="text-base font-medium text-gray-900">{selectedAppointment.customer.name}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    {selectedAppointment.customer.phone && (
                      <div>
                        <p className="text-sm text-gray-600">Phone</p>
                        <p className="text-base font-medium text-gray-900">{selectedAppointment.customer.phone}</p>
                      </div>
                    )}
                    {selectedAppointment.customer.email && (
                      <div>
                        <p className="text-sm text-gray-600">Email</p>
                        <p className="text-base font-medium text-gray-900">{selectedAppointment.customer.email}</p>
                      </div>
                    )}
                  </div>
                  {selectedAppointment.customer.loyaltyTier && (
                    <div>
                      <p className="text-sm text-gray-600">Loyalty Tier</p>
                      <span className={clsx(
                        'inline-block px-3 py-1 text-sm font-medium rounded-full',
                        selectedAppointment.customer.loyaltyTier === 'Platinum'
                          ? 'bg-purple-100 text-purple-700'
                          : selectedAppointment.customer.loyaltyTier === 'Gold'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                      )}>
                        {selectedAppointment.customer.loyaltyTier}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Vehicle Info */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Vehicle Information</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <p className="text-base font-medium text-gray-900">
                    {selectedAppointment.vehicle.year} {selectedAppointment.vehicle.make} {selectedAppointment.vehicle.model}
                  </p>
                  <p className="text-sm text-gray-600">VIN: {selectedAppointment.vehicle.vin}</p>
                  {selectedAppointment.vehicle.mileage && (
                    <p className="text-sm text-gray-600">Mileage: {selectedAppointment.vehicle.mileage}</p>
                  )}
                </div>
              </div>

              {/* Service Details */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Service Details</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  {selectedAppointment.serviceType && (
                    <div>
                      <p className="text-sm text-gray-600">Service Type</p>
                      <p className="text-base font-medium text-gray-900">{selectedAppointment.serviceType}</p>
                    </div>
                  )}
                  {selectedAppointment.estimatedDuration && (
                    <div>
                      <p className="text-sm text-gray-600">Estimated Duration</p>
                      <p className="text-base font-medium text-gray-900">{selectedAppointment.estimatedDuration}</p>
                    </div>
                  )}
                  {selectedAppointment.advisor && (
                    <div>
                      <p className="text-sm text-gray-600">Assigned Advisor</p>
                      <p className="text-base font-medium text-gray-900">{selectedAppointment.advisor}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Service History & Preferences */}
              {(selectedAppointment.customer.serviceHistory || selectedAppointment.customer.preferredServices) && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Personalized Experience</h3>
                  <div className="bg-cox-blue-50 rounded-lg p-4 space-y-3">
                    {selectedAppointment.customer.serviceHistory && (
                      <div>
                        <p className="text-sm text-gray-600">Service History</p>
                        <p className="text-base font-medium text-gray-900">
                          {selectedAppointment.customer.serviceHistory} previous visits
                          {selectedAppointment.customer.lastVisit && ` • Last visit: ${format(new Date(selectedAppointment.customer.lastVisit), 'MMM d, yyyy')}`}
                        </p>
                      </div>
                    )}
                    {selectedAppointment.customer.preferredServices && selectedAppointment.customer.preferredServices.length > 0 && (
                      <div>
                        <p className="text-sm text-gray-600 mb-2">Preferred Services</p>
                        <div className="flex flex-wrap gap-2">
                          {selectedAppointment.customer.preferredServices.map((service, idx) => (
                            <span
                              key={idx}
                              className="px-3 py-1 text-sm bg-cox-blue-600 text-white rounded-full"
                            >
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setShowCheckInModal(false);
                    setSelectedAppointment(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCompleteCheckIn}
                  className="px-6 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700 transition-colors flex items-center space-x-2"
                >
                  <CheckCircleIcon className="w-5 h-5" />
                  <span>Complete Check-In</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Chat Bot */}
      <FloatingChatBot pageContext={pageContext} />
    </div>
  );
}


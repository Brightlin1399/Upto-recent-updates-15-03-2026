import { Mail } from "lucide-react";
import { ArrowLeft, Phone, MapPin, Calendar, User } from 'lucide-react';
import { useNavigate } from "react-router-dom";
import { Navigate } from "react-router-dom";




interface ProfilePageProps {
  loggedInUser: {
    role: string;
    email: string;
    name?: string;
    phone?: string;
    location?: string;
    joinDate?: string;
  };
}

 export const ProfilePage = ({ loggedInUser }: ProfilePageProps) => {
  const navigate = useNavigate();

  const handleBackToHome = () => {
    navigate('/Home');
  };
  

 
  const userInfo = {
    name: loggedInUser.name ,
    role: loggedInUser.role,
    email: loggedInUser.email,
    phone: loggedInUser.phone || '+1 234 567 8900',
    location: loggedInUser.location || 'New York, USA',
    joinDate: loggedInUser.joinDate || 'January 2024'
  };
 


  return (
    <div className="min-h-screen bg-gray-100">
      {/* Back Button */}
      <div className="px-4 pt-4">
        <button
          onClick={handleBackToHome}
          className="flex items-center gap-2 px-4 py-2 text-[#005B6E] hover:bg-white rounded-lg transition-colors font-medium"
        >
          <ArrowLeft size={20} />
          <span>Back to Home</span>
        </button>
      </div>

      {/* Profile Page Content */}
      <div className="px-4 pb-8 pt-4 max-w-6xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          {/* Profile Header */}
          <div 
            className="p-10 text-white font-medium text-center bg-black"
            
          >
            <div className="w-32 h-32 bg-white rounded-full mx-auto mb-4 flex items-center justify-center shadow-xl">
              <User size={64} className="text-[#005B6E]" />
            </div>
            <h1 className="text-3xl font-bold mb-2">{userInfo.name}</h1>
            <p className="text-lg opacity-90">{userInfo.role}</p>
          </div>

          {/* Profile Details */}
          <div className="p-8">
            <h2 className="text-xl font-bold text-black mb-6 pb-2 border-b-2 border-[#D4AF37]">
              Profile Information
            </h2>

            <div className="grid gap-5">
             
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Mail size={24} className="text-[#005B6E]" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">Email Address</p>
                  <p className="text-base font-semibold text-gray-800">{userInfo.email}</p>
                </div>
              </div>

            
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Phone size={24} className="text-[#005B6E]" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">Phone Number</p>
                  <p className="text-base font-semibold text-gray-800">{userInfo.phone}</p>
                </div>
              </div>

            
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <MapPin size={24} className="text-[#005B6E]" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">Location</p>
                  <p className="text-base font-semibold text-gray-800">{userInfo.location}</p>
                </div>
              </div>

              
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Calendar size={24} className="text-[#005B6E]" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">Member Since</p>
                  <p className="text-base font-semibold text-gray-800">{userInfo.joinDate}</p>
                </div>
              </div>
            </div>

            
            <div className="flex gap-3 mt-8 flex-wrap">
              <button className="flex-1 min-w-[150px] px-6 py-3 bg-white text-black border-2  rounded-lg font-semibold hover:bg-white hover:text-black hover:border-black transition-colors hover:cursor-pointer">
                Edit Profile
              </button>
              <button className="flex-1 min-w-[150px] px-6 py-3 bg-white text-black border-2  rounded-lg font-semibold hover:bg-white hover:text-black hover:border-black transition-colors hover:cursor-pointer">
                Change Password
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
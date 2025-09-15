from unfold.sites import UnfoldAdminSite

class CustomAdminSites(UnfoldAdminSite):
	site_header = "Easy Go Express"
	site_title = "Easy Go Express"
	index_title = "Welcome to EasyGo Express"

custom_admin_site = CustomAdminSites
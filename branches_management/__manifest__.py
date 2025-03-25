# -*- coding: utf-8 -*-
#################################################################################

{
  "name"     :  "Branches Management",
  "summary"  :  """manage multiple branches """ ,
  "version"  :  "1.0.0",
  "author"   :  "Ahmed Amen",
  "depends"  :  [
      'base',
      'web',
                ],
  "data"     :  [
      'data/res_branch_data.xml',
     'security/security.xml',
     'security/ir.model.access.csv',
     'views/area.xml',
     'views/res_branch_view.xml',
     'views/menu_items.xml',
                ],
  "assets": {
      'web.assets_backend': [
          'branches_management/static/src/xml/branch_menu.xml',
          'branches_management/static/src/scss/branch_menu.scss',
          'branches_management/static/src/js/switch_branch.js',
          'branches_management/static/src/js/branch_service.js',
      ],
      'web.assets_qweb': [
      ],
  },
  "application"  :  True,
  "installable"  :  True,
  "auto_install" :  False,
}

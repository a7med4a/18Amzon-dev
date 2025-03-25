/** @odoo-module **/

import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownGroup } from "@web/core/dropdown/dropdown_group";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";

import { Component, useChildSubEnv, useState } from "@odoo/owl";
import { debounce } from "@web/core/utils/timing";
import { useService } from "@web/core/utils/hooks";

class BranchSelector {
    constructor(BranchService, toggleDelay) {
        this.BranchService = BranchService;
        this.selectedBranchesIds = BranchService.activeBranchIds;
        this.selectedCompaniesIds = BranchService.activeCompanyIds;
        this._debouncedApply = debounce(() => this._apply(), toggleDelay);
    }

    isBranchSelected(branchId) {
        return this.selectedBranchesIds.includes(branchId);
    }

    SwitchBranch(mode, branchId) {
        if (mode === "toggle") {
            if (this.selectedBranchesIds.includes(branchId) && this.selectedBranchesIds.length!=1) {
                this._deselectBranch(branchId);
            } else {
                this._selectBranch(branchId);
            }
            this._debouncedApply();
        } else if (mode === "loginto") {
            this.selectedBranchesIds.splice(0, this.selectedBranchesIds.length);
            this.selectedCompaniesIds.splice(0, this.selectedCompaniesIds.length);
            this._selectBranch(branchId);
            this._apply();
        }
    }

    _apply() {
        this.BranchService.setBranches(this.selectedBranchesIds, this.selectedCompaniesIds);
    }

    _selectCompany(companyId) {
        if (!this.selectedCompaniesIds.includes(companyId)) {
            this.selectedCompaniesIds.push(companyId);
        }
    }

    _selectBranch(branchId) {
        if (!this.selectedBranchesIds.includes(branchId)) {
            this.selectedBranchesIds.push(branchId);
            var company = this._getBranches(branchId);
            this._selectCompany(company)
        }
    }

    _deselectBranch(branchId) {
        if (this.selectedBranchesIds.includes(branchId)) {
            this.selectedBranchesIds.splice(this.selectedBranchesIds.indexOf(branchId), 1);
        }
    }

    _getBranches(branchId) {
        return this.BranchService.getBranch(branchId).company;
    }

}

export class SwitchBranchItem extends Component {
    static template = "web.SwitchBranchItem";
    static components = {DropdownItem, SwitchBranchItem };
    static props = {
        branch: {},
        level: { type: Number },
    };

    setup() {
        this.BranchService = useService("branch");
        this.BranchSelector = useState(this.env.BranchSelector);
    }

    get isBranchSelected() {
        return this.BranchSelector.isBranchSelected(this.props.branch.id);
    }

    get isBranchAllowed() {
        return this.props.branch.id in this.BranchService.allowedBranches;
    }

    get isCurrent() {
        return this.props.branch.id === this.BranchService.currentBranch.id;
    }

    logIntoBranch() {
        if (this.isBranchAllowed) {
            this.BranchSelector.SwitchBranch("loginto", this.props.branch.id);
        }
    }

    toggleBranch() {
        if (this.isBranchAllowed) {
            this.BranchSelector.SwitchBranch("toggle", this.props.branch.id);
        }
    }
}

export class SwitchBranchMenu extends Component {
    static template = "web.SwitchBranchMenu";
    static components = { Dropdown,DropdownGroup, DropdownItem, SwitchBranchItem };
    static props = {};
    static toggleDelay = 1000;

    setup() {
        this.BranchService = useService("branch");
        this.BranchSelector = useState(
            new BranchSelector(this.BranchService, this.constructor.toggleDelay)
        );
        useChildSubEnv({ BranchSelector: this.BranchSelector });
        this.state = useState({});
    }

    get isSingleBranch() {
        return Object.values(this.BranchService.allowedBranchesesWithAncestors ?? {}).length === 1;
    }
}

export const systrayItem = {
    Component: SwitchBranchMenu,
    isDisplayed(env) {
        const { allowedBranches } = env.services.branch;
        return Object.keys(allowedBranches).length > 1;
    },
};

registry.category("systray").add("SwitchBranchMenu", systrayItem, { sequence: 1 });

/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { UPDATE_METHODS } from "@web/core/orm_service";
import { cookie } from "@web/core/browser/cookie";
import { user } from "@web/core/user";
import { router } from "@web/core/browser/router";

const BIDS_HASH_SEPARATOR = "-";
const CIDS_HASH_SEPARATOR = "-";

function parseBranchIds(bids, separator = BIDS_HASH_SEPARATOR) {
    if (typeof bids === "string") {
        return bids.split(separator).map(Number);
    } else if (typeof bids === "number") {
        return [bids];
    }
    return [];
}

function formatBranchIds(bids, separator) {
    return bids.join(separator);
}

function computeActiveBranchIds(bids) {
    const { user_branches } = session;
    let activeBranchIds = bids || [];
    const availableBranchesFromSession = user_branches.allowed_branches;
    const notReallyAllowedBranches = activeBranchIds.filter(
        (id) => !(id in availableBranchesFromSession)
    );
    if (!activeBranchIds.length || (activeBranchIds.length && (activeBranchIds[0] === NaN || activeBranchIds[0] === 0)) ) {
        activeBranchIds = [user_branches.current_branch];
    }
    return activeBranchIds;
}

function getBranchIds() {
    let bids;
    const state = router.current;
    if ("bids" in state) {
        if (typeof state.bids === "string" && !state.bids.includes(BIDS_HASH_SEPARATOR)) {
            bids = parseBranchIds(state.bids, ",");
        } else {
            bids = parseBranchIds(state.bids);
        }
    } else if (cookie.get("bids")) {
        bids = parseBranchIds(cookie.get("bids"));
    }
    return bids || [];
}

function computeActiveCompanyIds(cids) {
    const { user_companies } = session;
    let activeCompanyIds = cids || [];
    const availableCompaniesFromSession = user_companies.allowed_companies;
    const notAllowedCompanies = activeCompanyIds.filter(
        (id) => !(id in availableCompaniesFromSession)
    );

    if (!activeCompanyIds.length || notAllowedCompanies.length) {
        activeCompanyIds = [user_companies.current_company];
    }
    return activeCompanyIds;
}

function getCompanyIds() {
    let cids;
    // backward compatibility, in old urls cid was still used.
    // deprecated as of saas-17.3
    const state = router.current;
    if ("cids" in state) {
        // backward compatibility s.t. old urls (still using "," as separator) keep working
        // deprecated as of 17.0
        if (typeof state.cids === "string" && !state.cids.includes(CIDS_HASH_SEPARATOR)) {
            cids = parseBranchIds(state.cids, ",");
        } else {
            cids = parseBranchIds(state.cids);
        }
    } else if (cookie.get("cids")) {
        cids = parseBranchIds(cookie.get("cids"));
    }
    return cids || [];
}

export const BranchService = {
    dependencies: ["company", "action", "orm"],
    start(env, {company, action, orm, branch }) {
        const allowedBranches = session.user_branches.allowed_branches;
        const allowedCompanies = session.user_companies.allowed_companies;
        const allowedBranchesesWithAncestors = {
            ...allowedBranches,
        };
        const activeBranchIds = computeActiveBranchIds(getBranchIds());
        const activeCompanyIds = computeActiveCompanyIds(getCompanyIds());

        // update browser data
        const bidsHash = formatBranchIds(activeBranchIds, BIDS_HASH_SEPARATOR);
        const cidsHash = formatBranchIds(activeCompanyIds, CIDS_HASH_SEPARATOR);
        router.replaceState({ bids: bidsHash, cids:cidsHash }, { lock: true });
        cookie.set("bids", activeBranchIds.join(BIDS_HASH_SEPARATOR));
        cookie.set("cids", activeCompanyIds.join(CIDS_HASH_SEPARATOR));
        user.updateContext({ allowed_branch_ids: activeBranchIds ,allowed_company_ids: activeCompanyIds});

        env.bus.addEventListener("RPC:RESPONSE", (ev) => {
            const { data, error } = ev.detail;
            const { model, method } = data.params;
            if (!error && model === "res.branch" && UPDATE_METHODS.includes(method)) {
                if (!browser.localStorage.getItem("running_tour")) {
                    action.doAction("reload_context");
                }
            }
        });

        return {
            allowedBranches,
            allowedBranchesesWithAncestors,

            get activeBranchIds() {
                return activeBranchIds;
            },
            get activeCompanyIds() {
                return activeCompanyIds;
            },

            get currentBranch() {
                return allowedBranches[activeBranchIds[0]];
            },

            getBranch(branchId) {
                return allowedBranchesesWithAncestors[branchId];
            },

            /**
             * @param {Array<>} BranchIds - List of Branches to log into
             */
            setBranches(BranchIds, companyIds) {
                const newBranchIds = BranchIds.length ? BranchIds : [activeBranchIds[0]];
                const bidsHash = formatBranchIds(newBranchIds, BIDS_HASH_SEPARATOR);
                const newCompanyIds = companyIds.length ? companyIds : [activeCompanyIds[0]];
                const cidsHash = formatBranchIds(newCompanyIds, CIDS_HASH_SEPARATOR);
                router.pushState({ bids: bidsHash , cids: cidsHash}, { lock: true });
                cookie.set("bids", formatBranchIds(newBranchIds));
                cookie.set("cids", formatBranchIds(newCompanyIds));
                browser.setTimeout(() => browser.location.reload()); // history.pushState is a little async
            },
        };
    },
};

registry.category("services").add("branch", BranchService);
